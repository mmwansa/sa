from api.common import Utils
import traceback


class FromSubmissionImportResult:
    def __init__(self):
        # The OdkForms imported.
        self.imported_forms = []
        # The Database Models imported (Event, Household, etc.)
        self.imported_models = []
        # The imported source rows.
        self.imported_data = []
        # Import process info message log.
        self.info_log = []
        # Import process error message log.
        self.errors = []

    def as_json(self):
        json = {
            "imported_forms": [],
            "imported_models": [],
            "imported_data": self.imported_data,
            "info_log": self.info_log,
            "errors": self.errors
        }
        for imported_form in self.imported_forms:
            id = imported_form if isinstance(imported_form, str) else imported_form.id
            json["imported_forms"].append({"id": id})

        for imported_model in self.imported_models:
            id = imported_model if isinstance(imported_model, str) else imported_model.id
            json["imported_models"].append({"id": id})

        return json

    def info(self, msg, console=True):
        self.info_log.append(msg)
        if console:
            print(msg)

    @property
    def has_errors(self):
        return len(self.errors) > 0

    def error(self, message, error=None, console=True):
        """
        Logs an error message with an optional exception and stack trace.

        Args:
            message (str): The error message to log.
            error (Exception): Optional. The exception to include in the log.
            console (bool): Whether to print the error to the console. Defaults to True.
        """
        if error is not None:
            stack_trace = ''.join(traceback.format_exception(type(error), value=error, tb=error.__traceback__))
            message = '{} {}'.format(message, stack_trace)
        self.errors.append(message)
        if console:
            print(message)
        return message

    def merge(self, other_result):
        for imported_form in other_result.imported_forms:
            self.add_imported_form(imported_form, console=False)
        for imported_model in other_result.imported_models:
            self.add_imported_model(imported_model, console=False)
        for imported_data in other_result.imported_data:
            self.add_imported_data(imported_data, console=False)
        for info in other_result.info_log:
            self.info(info, console=False)
        for error in other_result.errors:
            self.error(error, console=False)

    def add_imported_form(self, odk_form, console=False):
        odk_forms = Utils.to_list(odk_form)
        for odk_form in odk_forms:
            if odk_form not in self.imported_forms:
                self.imported_forms.append(odk_form)
            if console:
                self.info('Imported ODK Form: {} (id: {}) for ODK Project: {} (id: {})'.format(odk_form.name,
                                                                                               odk_form.id,
                                                                                               odk_form.odk_project.name,
                                                                                               odk_form.odk_project.id
                                                                                               ),
                          console=console)

    def add_imported_model(self, model, console=False):
        models = Utils.to_list(model)
        for model in models:
            if model not in self.imported_models:
                self.imported_models.append(model)
            if console:
                self.info('Imported {}: (id: {})'.format(model.__class__.__name__, model.id), console=console)

    def add_imported_data(self, imported_data, console=False, console_complete=False):
        imported_data = Utils.to_list(imported_data)
        for imported_data in imported_data:
            if imported_data not in self.imported_data:
                self.imported_data.append(imported_data)
            if console or console_complete:
                if console_complete:
                    self.info('Imported Form Submission: {}'.format(imported_data), console)
                else:
                    self.info('Imported Form Submission: {}...'.format(str(imported_data)[0:50]), console=console)
