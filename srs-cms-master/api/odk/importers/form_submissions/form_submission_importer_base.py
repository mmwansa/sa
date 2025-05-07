import os
from api.odk import OdkConfig
from api.odk.importers.form_submissions.form_submission_import_result import FromSubmissionImportResult
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.odk.transformers import TransformField
from api.common import Utils, TypeCaster
from django.conf import settings


class FromSubmissionImporterBase:
    def __init__(self, odk_form, odk_form_importer, child_importers=None, import_start_date=None, import_end_date=None,
                 form_submissions=None, out_dir=None, verbose=False):
        self.odk_config = OdkConfig.from_env()
        self.client = self.odk_config.client()
        self.odk_form = odk_form
        self.odk_form_importer = odk_form_importer
        self.child_importers = Utils.to_list(child_importers)
        self.import_start_date = import_start_date
        self.import_end_date = import_end_date
        self._form_submissions = Utils.to_list(form_submissions)
        self.odk_project = odk_form.odk_project
        self.out_dir = Utils.expand_path(out_dir) if out_dir else None
        self.verbose = verbose is True
        self.result = FromSubmissionImportResult()
        self._etl_mappings = None

    def validate_before_execute(self):
        """
        Validate before executing the import.

        Returns:
            True if valid, otherwise False.
        """
        if not self.odk_form_importer:
            self.result.error(
                'ODK Form Importer not set. {}: {} ({})'.format(
                    self.odk_form.__class__.__name__,
                    self.odk_form.name,
                    self.odk_form.id
                ), console=True)
            return False

        odk_form_importers = self.odk_form.get_odk_form_importers()
        if not odk_form_importers:
            self.result.error(
                'ODK Form Importers not set. {}}: {} ({})'.format(
                    self.odk_form.__class__.__name__,
                    self.odk_form.name,
                    self.odk_form.id
                ), console=True)
            return False

        for odk_form_importer in odk_form_importers:
            if not odk_form_importer.etl_document:
                self.result.error('ETL Document not set. {} {}'.format(
                    odk_form_importer.__class__.__name__,
                    odk_form_importer.id
                ), console=True)
                return False
            else:
                etl_mappings = self.get_etl_mappings()
                if not etl_mappings:
                    self.result.error('ETL Document Mappings not set or enabled. {}: {} ({})'.format(
                        odk_form_importer.etl_document.__class__.__name__,
                        odk_form_importer.etl_document.name,
                        odk_form_importer.etl_document.id
                    ), console=True)
                    return False
                else:
                    primary_key_mappings = [m for m in etl_mappings if m.is_primary_key]
                    if not primary_key_mappings:
                        self.result.error('ETL Document Mappings does not have primary key(s) set.. {}: {} ({})'.format(
                            odk_form_importer.etl_document.__class__.__name__,
                            odk_form_importer.etl_document.name,
                            odk_form_importer.etl_document.id
                        ), console=True)
                        return False
        return True

    def get_form_submissions(self):
        """
        Generator to get the form submissions from ODK Central for the OdkForm, version, and start/end dates.

        Returns:
            None
        """
        page_size = settings.ODK_API_FORM_SUBMISSION_PAGE_SIZE
        offset = 0
        while True:
            if self._form_submissions:
                form_submissions = self._form_submissions[offset:offset + page_size]
                form_submission_response = {
                    'value': form_submissions,
                    '@odata.count': len(form_submissions)
                }
            else:
                form_submission_response = self.client.submissions.get_table(
                    form_id=self.odk_form.xml_form_id,
                    project_id=self.odk_project.project_id,
                    count=True,
                    top=page_size,
                    skip=offset,
                    expand='*',
                    filter="__system/submissionDate ge '{}' and __system/submissionDate le '{}'".format(
                        self.import_start_date,
                        self.import_end_date)
                )

            current_page_submissions = form_submission_response.get('value', [])
            for form_submission in current_page_submissions:
                # Form Submissions cannot be filtered at the API by formVersion so manually filter here.
                form_version = self.get_value_from_record(
                    form_submission,
                    source_name='__system.formVersion',
                    _target_type=TypeCaster.TypeCode.STR)
                if form_version == self.odk_form.version:
                    yield form_submission
            if len(current_page_submissions) < page_size:
                break
            offset += page_size

    def get_etl_mapping_for(self, source_name=None, target_name=None):
        """
        Gets the EtlMapping for a source_name or target_name.

        Args:
            source_name: The source_name to find the mapping by.
            target_name: The target_name to find the mapping by.

        Returns:
            EtlMapping or None.
        """
        etl_mapping = next(
            (mapping for mapping in self.get_etl_mappings() if
             (target_name is None or mapping.target_name == target_name) and
             (source_name is None or mapping.source_name == source_name)
             ),
            None)
        return etl_mapping

    def get_etl_mappings(self):
        """
        Get the enabled EtlMappings for the OdkForm ordered by is_primary_key.

        Returns:
            List of EtlMappings.
        """
        if self._etl_mappings is None:
            self._etl_mappings = list(
                self.odk_form_importer.etl_document.etl_mappings.filter(is_enabled=True).order_by('-is_primary_key')
            )
        return self._etl_mappings

    def on_can_import(self, etl_record, form_submission):
        """
        Gets if the form submission can be imported.

        Args:
            etl_record: The ODK data record being imported.
            form_submission: The ODK form_submission.

        Returns:
            True to import otherwise False.
        """
        return True

    def on_new_model(self, model_class, etl_record, form_submission):
        """
        Instantiates a new model class.

        Args:
            model_class: The model class to instantiate.
            etl_record: The ODK data record being imported.
            form_submission: The ODK form_submission.

        Returns:
            A new instance of the model class.
        """
        return model_class()

    def on_set_model_attr(self, new_model, source_value, etl_mapping, etl_record, form_submission):
        """
        Sets the value for a model attribute.

        Args:
            new_model: The model instance being populated.
            source_value: The source value from the form_submission.
            etl_mapping: The ETL mapping.
            etl_record: The ODK data record being imported.
            form_submission: The ODK form_submission.

        Returns:
            None
        """
        setattr(new_model, etl_mapping.target_name, source_value)

    def on_cast_value(self, source_value, etl_mapping, etl_record, form_submission, new_model):
        """
        Cast a source value to a target value.

        Args:
            source_value: The source value from the form_submission.
            etl_mapping: The ETL mapping.
            etl_record: The ODK data record being imported.
            form_submission: The ODK form_submission.
            new_model: The model instance being populated.

        Returns:
            The value to set the field to.
        """
        return etl_mapping.cast_value(source_value)

    def on_before_save_model(self, new_model, etl_record, form_submission):
        """
        Called before saving a model instance.

        Args:
            new_model: The model instance being saved.
            etl_record: The ODK data record being imported.
            form_submission: The ODK form_submission.

        Returns:
            True if the model can be saved.
        """
        return True

    def on_after_save_model(self, new_model, etl_record, form_submission):
        """
        Called after saving a model instance.

        Args:
            new_model: The model instance that was saved.
            etl_record: The ODK data record being imported.
            form_submission: The ODK form_submission.

        Returns:
            None
        """
        pass

    def import_submissions(self, model_class):
        """
        Import the Submissions from ODK.

        Args:
            model_class (type): The class of the model to import.

        Returns:
            FromSubmissionImportResult: The result of the import operation.
        """
        try:
            etl_mappings = self.get_etl_mappings()

            if self.out_dir:
                Utils.ensure_dirs(self.out_dir)

            child_importers_form_submissions = []

            for form_submission in self.get_form_submissions():
                try:
                    child_importers_form_submissions.append(form_submission)

                    if self.odk_form_importer.etl_document.source_root:
                        import_records = self.get_value_from_record(
                            form_submission,
                            source_name=self.odk_form_importer.etl_document.source_root,
                            _target_type=TypeCaster.TypeCode.LIST
                        ) or []
                    else:
                        import_records = [form_submission]

                    for etl_record in import_records:
                        if self.out_dir:
                            self._save_form_submission_json(form_submission, etl_record, model_class)

                        if not self.on_can_import(etl_record, form_submission):
                            continue

                        new_model = self.on_new_model(model_class, etl_record, form_submission)
                        if new_model is None:
                            self.result.error('Could not create model class: {}'.format(model_class.__name__))
                            continue

                        primary_keys_set = False
                        primary_keys = None
                        existing_model = None
                        etl_mapping_error = None
                        for etl_mapping in etl_mappings:
                            # Once all the primary key values are set check for an existing model and stop mapping if found.
                            if not primary_keys_set:
                                primary_keys, primary_keys_set = self._get_primary_keys(new_model)
                                if primary_keys_set:
                                    existing_model = self._find_model(new_model)
                                    if existing_model:
                                        break

                            has_source_field = etl_mapping.has_source_name(etl_record)
                            has_target_field = hasattr(new_model, etl_mapping.target_name)

                            if etl_mapping.is_required and not has_source_field:
                                etl_mapping_error = 'ETL Record does not have a field named {}. ETL Record: {}'.format(
                                    etl_mapping.source_name,
                                    etl_record
                                )
                                break
                            if not has_target_field:
                                etl_mapping_error = 'ETL Target: {} does not have a field named {}'.format(
                                    new_model.__class__,
                                    etl_mapping.target_name
                                )
                                break

                            source_value = etl_mapping.get_target_value(etl_record, cast=False, transform=False)
                            source_value = self.on_cast_value(source_value, etl_mapping, etl_record, form_submission,
                                                              new_model)

                            if etl_mapping.transform:
                                source_value = etl_mapping.transform_value(source_value)

                            self.on_set_model_attr(new_model, source_value, etl_mapping, etl_record, form_submission)

                        if etl_mapping_error is not None:
                            self.result.error(etl_mapping_error, console=True)
                        else:
                            existing_model = (
                                existing_model if primary_keys_set else self._find_model(new_model)
                            )
                            if existing_model is None:
                                can_save = self.on_before_save_model(new_model, etl_record, form_submission)

                                if can_save:
                                    try:
                                        new_model.save()
                                        self.result.add_imported_model(new_model, console=True)
                                        self.result.add_imported_data(form_submission, console=self.verbose)
                                        self.on_after_save_model(new_model, etl_record, form_submission)
                                    except Exception as ex:
                                        self.result.error(
                                            'Could not create {} for: {}, Error: {}'.format(model_class.__name__,
                                                                                            primary_keys,
                                                                                            str(ex)),
                                            console=True
                                        )
                            else:
                                self.result.info('Model already exists. Skipping: {} ({})'.format(
                                    existing_model.__class__.__name__,
                                    existing_model.id
                                ), console=True)

                    if len(child_importers_form_submissions) >= settings.ODK_API_FORM_SUBMISSION_PAGE_SIZE:
                        self._run_child_importers(child_importers_form_submissions)
                        child_importers_form_submissions.clear()
                except Exception as ex:
                    self.result.error('Error importing submission: {}.'.format(form_submission),
                                      error=ex,
                                      console=True)

            self._run_child_importers(child_importers_form_submissions)
            self.result.add_imported_form(self.odk_form, console=self.verbose)
        except Exception as ex:
            self.result.error('Error executing import_submissions.', error=ex, console=True)
        return self.result

    def get_key_from_record(self, record):
        """
        Gets the 'key' ('__id') value for a given record.

        Args:
            record: The ODK data record.

        Returns:
            The key value or None.
        """
        key = self.get_value_from_record(
            record,
            source_name='__id',
            target_name='key',
            _target_type=TypeCaster.TypeCode.STR,
            _transform=TransformField(name='replace', args=['uuid:', ''])
        )
        return key

    def get_model_or_try_execute_importer(self, model_class, importer, form_submission):
        """
        Gets the existing model record for 'model_class' from the 'form_submission' __id/key.
        If the model does not exist this will attempt to execute the importer for the model_class.
        This is meant to be used by child importers to import the parent model.

        Args:
            model_class: The model type to get or import.
            importer: The importer name to use if the model does not exist.
            form_submission: The form submission to be imported.

        Returns:
            The existing or newly imported model, or None.
        """
        key = self.get_key_from_record(form_submission)
        model = model_class.find_by(key=key)
        if model is None:
            odk_form_importer = self.odk_form.get_odk_form_importer(importer)
            if odk_form_importer:
                self.result.info('Attempting Import for: {} key: {}'.format(model_class.__name__, key), console=True)
                model_importer = FromSubmissionImporterFactory.get_importer(odk_form_importer,
                                                                            self.odk_form,
                                                                            odk_form_importer,
                                                                            import_start_date=self.import_start_date,
                                                                            import_end_date=self.import_end_date,
                                                                            form_submissions=form_submission,
                                                                            out_dir=self.out_dir,
                                                                            verbose=self.verbose)
                importer_result = model_importer.execute()
                self.result.merge(importer_result)
                model = model_class.find_by(key=key)
                if model is None:
                    self.result.error('Could not create {} for key: {}'.format(model_class.__name__, key), console=True)
            else:
                self.result.error('OdkForm: {} does not have importer: {}'.format(
                    self.odk_form.id,
                    importer
                ), console=True)
        return model

    def get_value_from_record(self, record, source_name=None, target_name=None,
                              _target_type=None, _transform=None):
        """
        Gets a field value from a record.
        Provide either the source_name or target_name of the field to get (source_name is preferred).
        If the field has an EtlMapping, it will be used to get/cast/transform the value.
        If the EtlMapping does not exist and source_name has been set, get the value of 'source_name'
        from the form_submission and cast and transform the value (if _target_type and _transform are set).

        Args:
            record: The record to get the value from.
            source_name: The source_name of the field to get the value from.
            target_name: The target_name of the field to get the value from.
            _target_type: (Optional) The TypeCaster.TypeCode to cast the value to.
            _transform: (Optional) The TransformField or JSON to transform the value.

        Returns:
            The value or None.
        """
        etl_mapping = self.get_etl_mapping_for(source_name=source_name, target_name=target_name)
        if etl_mapping:
            value = etl_mapping.get_target_value(record, cast=True, transform=True)
        elif source_name is not None and Utils.has_field(record, source_name):
            value = Utils.get_field(record, source_name)
            if _target_type is not None:
                value = TypeCaster.cast(value, _target_type)
            if _transform is not None:
                value = TransformField.get(_transform).transform(value)
        else:
            value = None
        return value

    def _run_child_importers(self, form_submissions):
        """
        Execute each child importer with the supplied form submissions.

        Args:
            form_submissions: The ODK form submissions to pass to the child importers.

        Returns:
            OdkImportResult or None.
        """
        form_submissions = Utils.to_list(form_submissions)
        if len(form_submissions) > 0:
            run_child_importers_result = FromSubmissionImportResult()

            for odk_child_importer in self.child_importers:
                self.result.info("")
                self.result.info('Executing Child Importer: {}'.format(odk_child_importer.importer),
                                 console=self.verbose)
                child_importer = FromSubmissionImporterFactory.get_importer(odk_child_importer,
                                                                            self.odk_form,
                                                                            odk_child_importer,
                                                                            import_start_date=self.import_start_date,
                                                                            import_end_date=self.import_end_date,
                                                                            form_submissions=form_submissions,
                                                                            out_dir=self.out_dir,
                                                                            verbose=self.verbose)
                child_importer_result = child_importer.execute()
                run_child_importers_result.merge(child_importer_result)

            self.result.merge(run_child_importers_result)
            return run_child_importers_result
        else:
            return None

    def _find_model(self, model):
        """
        Finds an existing model in the database based on the EtlMapping primary keys.

        Args:
            model: The model to check.
            etl_mappings: EtlMappings for the model class.

        Returns:
            The existing model or None.
        """
        filter_kwargs, all_pks_set = self._get_primary_keys(model)
        if not all_pks_set:
            raise ValueError('Missing primary key values.')
        return model.__class__.find_by(**filter_kwargs)

    def _get_primary_keys(self, model):
        etl_mappings = self.get_etl_mappings()
        pk_names = [p.target_name for p in etl_mappings if p.is_primary_key]
        if not pk_names:
            raise ValueError('Primary key mappings not defined for: {}'.format(model.__class__))

        pk_kwargs = {pk_name: getattr(model, pk_name, None) for pk_name in pk_names}
        all_pks_set = all(pk_kwargs.values())
        return pk_kwargs, all_pks_set

    def _save_form_submission_json(self, form_submission, etl_record, model_class):
        submission_key = self.get_key_from_record(form_submission)
        out_filename = os.path.join(self.out_dir,
                                    'form-submission-{}-{}-{}.json'.format(self.odk_form.version,
                                                                           model_class.__name__,
                                                                           submission_key))
        Utils.save_json(form_submission, out_filename)

        if form_submission != etl_record:
            etl_key = self.get_key_from_record(etl_record)
            out_filename = os.path.join(self.out_dir,
                                        'form-submission-{}-{}-{}-{}.json'.format(self.odk_form.version,
                                                                                  model_class.__name__,
                                                                                  submission_key,
                                                                                  etl_key))
            Utils.save_json(etl_record, out_filename)
