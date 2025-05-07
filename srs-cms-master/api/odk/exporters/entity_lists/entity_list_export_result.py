from api.common import Utils
import traceback


class EntityListExportResult:
    def __init__(self):
        # The OdkEntityLists exported.
        self.exported_entity_lists = []
        # The Database Models exported (Death, etc.)
        self.exported_models = []
        # Export process info message log.
        self.info_log = []
        # Export process error message log.
        self.errors = []

    def as_json(self):
        json = {
            "exported_entity_lists": [],
            "exported_models": [],
            "info_log": self.info_log,
            "errors": self.errors
        }
        for entity_list in self.exported_entity_lists:
            id = entity_list if isinstance(entity_list, str) else entity_list.id
            json["exported_entity_lists"].append({"id": id})

        for exported_model in self.exported_models:
            id = exported_model if isinstance(exported_model, str) else exported_model.id
            json["exported_models"].append({"id": id})

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
        for exported_entity_list in other_result.exported_entity_lists:
            self.add_exported_entity_list(exported_entity_list, console=False)
        for exported_model in other_result.exported_models:
            self.add_exported_model(exported_model, console=False)
        for info in other_result.info_log:
            self.info(info, console=False)
        for error in other_result.errors:
            self.error(error, console=False)

    def add_exported_entity_list(self, odk_entity_list, console=False):
        odk_entity_lists = Utils.to_list(odk_entity_list)
        for odk_entity_list in odk_entity_lists:
            if odk_entity_list not in self.exported_entity_lists:
                self.exported_entity_lists.append(odk_entity_list)
            if console:
                self.info('Exported ODK Entity List: {} (id: {}) for ODK Project: {} (id: {})'.format(
                    odk_entity_list.name,
                    odk_entity_list.id,
                    odk_entity_list.odk_project.name,
                    odk_entity_list.odk_project.id,
                ),
                    console=console)

    def add_exported_model(self, model, console=False):
        models = Utils.to_list(model)
        for model in models:
            if model not in self.exported_models:
                self.exported_models.append(model)
            if console:
                self.info('Exported {}: (id: {})'.format(model.__class__.__name__, model.id), console=console)
