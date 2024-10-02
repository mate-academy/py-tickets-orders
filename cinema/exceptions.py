from rest_framework.exceptions import APIException


class InvalidIdException(APIException):
    status_code = 400
    default_detail = "At least one of provided IDs is not valid"
    default_code = "invalid_id"
