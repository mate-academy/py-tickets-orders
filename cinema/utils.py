class ParamsToIntsMixin:
    @staticmethod
    def _params_to_ints(query_params):
        return [int(str_id) for str_id in query_params.split(",")]
