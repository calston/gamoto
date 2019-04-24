# CA management
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dh
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

import datetime
import uuid
import os


class CertificateAuthority(object):
    """
    Certificate authority class
    """
    def __init__(self, ou, org, email, country, province, city, key_path=None,
                 validity=3653):
        """
        Construct a CertificateAuthority object
        parameters:
            org: Organisation name
            ou: Organisation unit
            email: Email address
            country: Country
            province: Province
            city: City
            key_path (kw): Path to store and retrieve PKI
                           default - Current working directory
            validity (kw): Certificate validity in days
                           default - 3653 (~10 years)
        """
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
            x509.NameAttribute(NameOID.LOCALITY_NAME, city),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email)
        ]

        self.ca_key_path = os.path.join(self.key_path, "ca.key")
        self.ca_cert_path = os.path.join(self.key_path, "ca.crt")

        self.validity_time = datetime.timedelta(validity, 0, 0)

    def createDH(self, key_size=2048):
        """
        Generate Diffie-Hellman key
        """
        filename = os.path.join(self.key_path, "dh%s.pem" % key_size)
        if os.path.exists(filename):
            return False

        parameters = dh.generate_parameters(generator=2, key_size=key_size,
                                            backend=default_backend())
        dhbytes = parameters.parameter_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.ParameterFormat.PKCS3
        )

        with open(filename, "wb") as f:
            f.write(dhbytes)

        return True

    def getCA(self):
        """
        Load the default CA keys
        """
        if (os.path.exists(self.ca_key_path) and os.path.exists(
                self.ca_cert_path)):
            with open(self.ca_cert_path, "rb") as cafile:
                ca_cert = x509.load_pem_x509_certificate(cafile.read(),
                                                         default_backend())

            with open(self.ca_key_path, "rb") as keyfile:
                private_key = serialization.load_pem_private_key(
                    keyfile.read(),
                    password=None,
                    backend=default_backend()
                )

            return (ca_cert, private_key)
        else:
            raise Exception("CA does not exist")

    def createCA(self, cn):
        """
        Create a CA with name cn
        """
        if (os.path.exists(self.ca_key_path) and os.path.exists(
                self.ca_cert_path)):
            return False

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        common_name = x509.NameAttribute(NameOID.COMMON_NAME, cn)
        now = datetime.datetime.utcnow()

        sn = x509.Name(self.x509params + [common_name])

        builder = x509.CertificateBuilder().subject_name(
            sn
        ).issuer_name(
            sn
        ).not_valid_before(
            now - datetime.timedelta(0, 1, 0)
        ).not_valid_after(
            now + self.validity_time
        ).serial_number(
            int(uuid.uuid4())
        ).public_key(
            public_key
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(
                private_key.public_key()),
            critical=False
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(
                private_key.public_key()),
            critical=False
        )

        certificate = builder.sign(
            private_key=private_key, algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        with open(self.ca_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(self.ca_cert_path, "wb") as f:
            f.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM,
            ))

        return True

    def getCSR(self, cn):
        """
        Retrieve a CSR with name cn
        """
        csr_path = os.path.join(self.key_path, "%s.csr" % cn)

        if os.path.exists(csr_path):
            with open(csr_path, "rb") as csrfile:
                csr = x509.load_pem_x509_csr(csrfile.read(), default_backend())
            return csr
        else:
            raise Exception("CSR does not exist")

    def createCSR(self, cn):
        """
        Create a CSR with name cn
        """
        key_path = os.path.join(self.key_path, "%s.key" % cn)
        csr_path = os.path.join(self.key_path, "%s.csr" % cn)

        if (os.path.exists(key_path) and os.path.exists(csr_path)):
            return False

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        common_name = x509.NameAttribute(NameOID.COMMON_NAME, cn)

        builder = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name(self.x509params + [common_name])
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(cn),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())

        # Write key
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Write CSR
        with open(csr_path, "wb") as f:
            f.write(builder.public_bytes(serialization.Encoding.PEM))

        return True

    def signCSR(self, cn, server=False):
        """
        Sign a CSR of name cn. Set server kw to True if this is for TLS
        server validation
        """
        assert isinstance(server, bool)

        cert_path = os.path.join(self.key_path, "%s.crt" % cn)

        if os.path.exists(cert_path):
            return False

        ca_cert, private_key = self.getCA()
        csr = self.getCSR(cn)

        now = datetime.datetime.utcnow()
        if server:
            extension = ExtendedKeyUsageOID.SERVER_AUTH
        else:
            extension = ExtendedKeyUsageOID.CLIENT_AUTH

        certificate = x509.CertificateBuilder().subject_name(
            csr.subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            csr.public_key()
        ).serial_number(
            int(uuid.uuid4())
        ).not_valid_before(
            now - datetime.timedelta(0, 1, 0)
        ).not_valid_after(
            now + self.validity_time
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=False
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(
                private_key.public_key()),
            critical=False
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(
                private_key.public_key()),
            critical=False
        ).add_extension(
            x509.ExtendedKeyUsage([extension]),
            critical=False,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=server,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=False
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(cn),
            ]),
            critical=False,
        ).sign(
            private_key=private_key, algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        with open(cert_path, "wb") as f:
            f.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM,
            ))

        return True
