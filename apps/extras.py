from datetime import datetime, timedelta

from django.db import models

from apps.matricula.models import Matricula, Pension
from sigestscolar.settings import ADMINISTRADOR_ID
from cryptography.hazmat.primitives.ciphers.algorithms import AES as Algorithm
from cryptography.hazmat.primitives.ciphers.modes import ECB as Mode
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher
from os import urandom


class ModeloBase(models.Model):
    """ Modelo base para todos los modelos del proyecto """
    from django.contrib.auth.models import User
    status = models.BooleanField(default=True)
    usuario_creacion = models.ForeignKey(User, related_name='+', blank=True, null=True, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    usuario_modificacion = models.ForeignKey(User, related_name='+', blank=True, null=True, on_delete=models.PROTECT)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        usuario = None
        if len(args):
            usuario = args[0].user.id
        if self.id:
            self.usuario_modificacion_id = usuario if usuario else ADMINISTRADOR_ID
            self.fecha_modificacion = datetime.now()
        else:
            self.usuario_creacion_id = usuario if usuario else ADMINISTRADOR_ID
            self.fecha_creacion = datetime.now()
        models.Model.save(self)

    class Meta:
        abstract = True


def null_to_numeric(valor, decimales=None):
    if decimales:
        return round((valor if valor else 0), decimales)
    return valor if valor else 0


class PrimaryKeyEncryptor:
    def __init__(self, secret: str):
        secret_bytes = bytes.fromhex(secret)

        if len(secret_bytes) != 16:
            raise ValueError('The secret for the PrimaryKeyEncryptor must be 16 bytes in hexadecimal format')

        algorithm = Algorithm(secret_bytes)
        mode = Mode()

        self.cipher = Cipher(algorithm, mode, backend=default_backend())

    @staticmethod
    def generate_secret() -> str:
        return urandom(16).hex()

    def encrypt(self, primary_key: int) -> str:
        primary_key_bytes = primary_key.to_bytes(8, byteorder='big')

        encryptor = self.cipher.encryptor()

        cipher_bytes = encryptor.update(primary_key_bytes * 2) + encryptor.finalize()

        return cipher_bytes.hex()

    def decrypt(self, encrypted_primary_key: str) -> int:
        cipher_bytes = bytes.fromhex(encrypted_primary_key)

        if len(cipher_bytes) != 16:
            raise ValueError('The encrypted primary key must be 16 bytes in hexadecimal format')

        decryptor = self.cipher.decryptor()

        plain_bytes = decryptor.update(cipher_bytes) + decryptor.finalize()

        if plain_bytes[:8] != plain_bytes[8:]:
            raise ValueError('The encrypted primary key is invalid')

        return int.from_bytes(plain_bytes[:8], byteorder='big')


class Item:
    def encoded_id(self, id):
        import base64
        return base64.b64encode(str(id))

    def decode_id(self, id):
        import base64
        return base64.b64decode(id)


def crear_matricula(inscripcion):
    valores = inscripcion.curso.configuracion_valores()
    # fecha maxima de pago 15 dias despues de la inscripcion
    fechamaxima = datetime.now() + timedelta(days=15)
    matricula = Matricula(inscripcion=inscripcion, observaciones='Ninguna', fecha=datetime.now(), fechatope=fechamaxima)
    matricula.save()
    fecha_primera_persion = inscripcion.curso.periodo.inicioactividades

    for cantidad in valores.numeropensiones:
        pension = Pension()
