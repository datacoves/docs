"""Base class for all DataCoves models"""

from django.db import models


class DatacovesModel(models.Model):
    """All models in DataCoves should extend this as a base.  Anything
    that should be common to all models can be put in here.  Please use
    this sparingly and carefully."""

    class Meta:
        abstract = True

    def is_relation_cached(self, relation_name: str) -> bool:
        """This checks to see if 'relation_name' is loaded in our model's
        cache.  This is useful for optimizations where we could loop over
        cache instead of doing a SQL query in certain cases."""

        # This can show up in potentially two places.  _state is for one
        # to one or one to many relations, _prefetched_objects_cache is
        # for many-to-many or reverse relations.
        #
        # The model object will not have _prefetched_objects_cache by
        # default so always check for the field's existance first.
        return relation_name in self._state.fields_cache or (
            hasattr(self, "_prefetched_objects_cache")
            and relation_name in self._prefetched_objects_cache
        )
