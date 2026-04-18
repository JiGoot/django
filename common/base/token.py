import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

'''
secrets.token_hex(20) → 40 chars → max_length=40, 160-bit
secrets.token_hex(32) → 64 chars → max_length=64,  256-bit
secrets.token_hex(64) → 128 chars → max_length=128, 512-bit

Modern recommendation
For stronger tokens:
    `secrets.token_hex(32)  # 64 chars, 256-bit`

- More secure (256-bit vs 160-bit)
- Slightly longer, but storage is trivial
- Future-proof for high-security applications
'''
class AbstractToken(models.Model):
    key = models.CharField(_("Key"), max_length=64, unique=True, db_index=True)
    used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")
    
    @classmethod
    def generate_key(cls):
        return secrets.token_hex(32)

    def __str__(self):
        return self.key
