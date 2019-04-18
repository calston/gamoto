# CA management
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dh
from cryptography.x509.oid import NameOID

import datetime
import uuid
import os


class CertificateAuthority(object):
    def __init__(self, ou, org, email, country, province, city, key_path=None):
        if key_path:
            self.key_path = key_path
        else:
            self.key_path = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))

        if not os.path.exists(self.key_path):
            raise Exception("Key path does not exist")

        self.x509params = [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, ou),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, org),
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, province),
            x509.NameAttribute(NameOID.LOCALITY_NAME, city)
        ]

    def createDH(self, key_size=2048):
        filename = os.path.join(self.key_path, "dh.pem")
        if os.path.exists(filename):
            return False

        parameters = dh.generate_parameters(generator=2, key_size=key_size,
                                            backend=default_backend())
        dhbytes = parameters.generate_private_key().private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        with open(filename, "wb") as f:
            f.write(dhbytes)

        return True

    def createCA(self, cn):
        key_path = os.path.join(self.key_path, "ca.key")
        cert_path = os.path.join(self.key_path, "ca.crt")

        if (os.path.exists(key_path) and os.path.exists(cert_path)):
            return False

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        common_name = x509.NameAttribute(NameOID.COMMON_NAME, cn)
        now = datetime.datetime.today()

        builder = x509.CertificateBuilder().subject_name(
            x509.Name(self.x509params + [common_name])
        ).issuer_name(
            x509.Name([common_name])
        ).not_valid_before(
            now - datetime.timedelta(1, 0, 0)
        ).not_valid_after(
            now + datetime.timedelta(3650, 0, 0)
        ).serial_number(
            int(uuid.uuid4())
        ).public_key(
            public_key
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )

        certificate = builder.sign(
            private_key=private_key, algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(cert_path, "wb") as f:
            f.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM,
            ))

        return True

    def createCSR(self, cn):
        key_path = os.path.join(self.key_path, "%s.key" % cn)
        cert_path = os.path.join(self.key_path, "%s.crt" % cn)

        if (os.path.exists(key_path) and os.path.exists(cert_path)):
            return False

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # public_key = private_key.public_key()

        common_name = x509.NameAttribute(NameOID.COMMON_NAME, cn)

        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name(self.x509params + [common_name])
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(cn),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        assert csr is not None

        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        return True
