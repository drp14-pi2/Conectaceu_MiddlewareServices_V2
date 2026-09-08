"""Profiles to exclude mapper"""
from src.data.models.profiles_to_exclude_model import ProfilesToExcludeModel
from src.domain.schemas.profiles_to_exclude import ProfilesToExclude

class ProfilesToExcludeMapper:
    @staticmethod
    def model_to_schema(model: ProfilesToExcludeModel) -> ProfilesToExclude:
        return ProfilesToExclude.model_validate(model)
