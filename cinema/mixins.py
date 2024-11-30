class ParamsToIntMixin:
    @staticmethod
    def _params_to_int(qs):
        return [int(str_id) for str_id in qs.split(",")]
