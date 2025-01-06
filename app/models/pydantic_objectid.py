from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class PydanticObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Validation function for ObjectId
        def validate(value: str) -> ObjectId:
            if not ObjectId.is_valid(value):
                raise ValueError(f"Invalid ObjectId: {value}")
            return ObjectId(value)

        # Generate schema using a callable validator
        return core_schema.no_info_after_validator_function(
            validate, core_schema.str_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetCoreSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "objectid"}

    def __str__(self):
        return str(self)
