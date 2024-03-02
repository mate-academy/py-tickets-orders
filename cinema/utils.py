class ParamsToIntsMixin:
    @staticmethod
    def _params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]
