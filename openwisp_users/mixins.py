"""
mixins used by other openwisp components to implement multi-tenancy
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ValidateOrgMixin(object):
    """
    - implements ``_validate_org_relation`` method
    """
    def _validate_org_relation(self, rel, field_error='organization'):
        """
        if the relation is owned by a specific organization
        this object must be related to the same organization
        """
        # avoid exceptions caused by the relation not being set
        if not hasattr(self, rel):
            return
        rel = getattr(self, rel)
        if rel and rel.organization_id and str(self.organization_id) != str(rel.organization_id):
            message = _('Please ensure that the organization of this {object_label} '
                        'and the organization of the related {related_object_label} match.')
            message = message.format(object_label=self._meta.verbose_name,
                                     related_object_label=rel._meta.verbose_name)
            raise ValidationError({field_error: message})

    def _validate_org_reverse_relation(self, rel, field_error='organization'):
        try:
            old_org = self.__class__.objects.get(pk=self.pk).organization
            if old_org != self.organization:
                count = eval('self.__class__.objects.get(pk=self.pk).{0}_set.count()'.format(rel))
                if count > 0:
                    message = _('organization cannot be changed because {0}'
                                ' objects as still related to it'.format(count))
                    raise ValidationError({field_error: message})
        except self.__class__.DoesNotExist:
            return


class OrgMixin(ValidateOrgMixin, models.Model):
    """
    - adds a ``ForeignKey`` field to the ``Organization`` model
      (the relation cannot be NULL)
    - implements ``_validate_org_relation`` method
    """
    organization = models.ForeignKey('openwisp_users.Organization',
                                     verbose_name=_('organization'),
                                     on_delete=models.CASCADE)

    class Meta:
        abstract = True


class ShareableOrgMixin(OrgMixin):
    """
    like ``OrgMixin``, but the relation can be NULL, in which
    case it means that the object can be shared between multiple organizations
    """
    class Meta:
        abstract = True


_org_field = ShareableOrgMixin._meta.get_field('organization')
_org_field.blank = True
_org_field.null = True
