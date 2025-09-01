#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

import json
import os
import random
import string

import pytest
from obs import (
    ObsClient,
    CustomDomainConfiguration
)
from conftest import test_config

right_certificate = """-----BEGIN CERTIFICATE-----
MIIGrTCCBZWgAwIBAgIMAxuwBcg57I1h4JOEMA0GCSqGSIb3DQEBCwUAMFAxCzAJ
BgNVBAYTAkJFMRkwFwYDVQQKExBHbG9iYWxTaWduIG52LXNhMSYwJAYDVQQDEx1H
bG9iYWxTaWduIFJTQSBPViBTU0wgQ0EgMjAxODAeFw0yNDA1MDYwMzE3MTdaFw0y
NTA2MDcwMzE3MTZaMH4xCzAJBgNVBAYTAkNOMRIwEAYDVQQIDAnmtZnmsZ/nnIEx
EjAQBgNVBAcMCeWugeazouW4gjEtMCsGA1UECgwk5rWZ5rGf5p6B5rCq5pm66IO9
56eR5oqA5pyJ6ZmQ5YWs5Y+4MRgwFgYDVQQDDA8qLnplZWtybGlmZS5jb20wggEi
MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCglDA0tnCPqgzUgP51IPu01Xs3
a3pgKYhjglGzORtAP41WLpy+ve0EhLxllZrQkMCcsz+eWCA/oxH0iSlyFi78cTxA
EQgJ02kBIjIopzxJaWGefjadItPqRqMTTpEHX0nxp+3lOim78YrE3IKcUQbxNT2C
q7dx5yMsD6g8i2VyLaw7JkweIlVeCkfUTLqIskrG3S/MLqK7UE2KrqD/QeIWayFc
UxrrF3ETiJkn+YUA2ZTuQ/01wLokVAC9Ysc87BvSXhr5UMFEGJUhY/HJXkv3V8ML
2aEWdOGrSYUNKVd+4vKnJuXYIJLcN7ZikqeOpM/0+V5kQQSankgVxmHvwxB1AgMB
AAGjggNXMIIDUzAOBgNVHQ8BAf8EBAMCBaAwDAYDVR0TAQH/BAIwADCBjgYIKwYB
BQUHAQEEgYEwfzBEBggrBgEFBQcwAoY4aHR0cDovL3NlY3VyZS5nbG9iYWxzaWdu
LmNvbS9jYWNlcnQvZ3Nyc2FvdnNzbGNhMjAxOC5jcnQwNwYIKwYBBQUHMAGGK2h0
dHA6Ly9vY3NwLmdsb2JhbHNpZ24uY29tL2dzcnNhb3Zzc2xjYTIwMTgwVgYDVR0g
BE8wTTBBBgkrBgEEAaAyARQwNDAyBggrBgEFBQcCARYmaHR0cHM6Ly93d3cuZ2xv
YmFsc2lnbi5jb20vcmVwb3NpdG9yeS8wCAYGZ4EMAQICMD8GA1UdHwQ4MDYwNKAy
oDCGLmh0dHA6Ly9jcmwuZ2xvYmFsc2lnbi5jb20vZ3Nyc2FvdnNzbGNhMjAxOC5j
cmwwKQYDVR0RBCIwIIIPKi56ZWVrcmxpZmUuY29tgg16ZWVrcmxpZmUuY29tMB0G
A1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjAfBgNVHSMEGDAWgBT473/yzXhn
qN5vjySNiPGHAwKz6zAdBgNVHQ4EFgQUWNyNg+4HOZZxKYxh/Vz+MS7fIh0wggF9
BgorBgEEAdZ5AgQCBIIBbQSCAWkBZwB1AKLjCuRF772tm3447Udnd1PXgluElNcr
XhssxLlQpEfnAAABj0vn5jcAAAQDAEYwRAIgJIn6bk7wipY+5Z5+SYfaxmOrgE1B
uMsLQW7L8JKPsXYCIDN57d9gJFsy+VkqdqEAVY69uQWtxJVzzAI+J7atLb71AHUA
TnWjJ1yaEMM4W2zU3z9S6x3w4I4bjWnAsfpksWKaOd8AAAGPS+fnSwAABAMARjBE
AiBNswzZVDrAP4D2VLbocXE9JsJb2bJpiptrF+bMrjGLuwIgaBGClOR6nEwcvhIu
8voz1q8Q6bEgMBQXW2B88IyG9p0AdwDgkrP8DB3I52g2H95huZZNClJ4GYpy1nLE
sE2lbW9UBAAAAY9L5+dfAAAEAwBIMEYCIQDT3R7jguKkZkUqtPlwyzxnmmloQkjp
PAgGP2QdVKNm8wIhALP9JnI9Q2wiA2154REakvaqBDV0uy/2W5AVmXG6GOO2MA0G
CSqGSIb3DQEBCwUAA4IBAQCUj6Yer+WJiNXSIu7zTRtIDp6CW18IEvEnYx/H2Gqp
EEMrCBECxzzksyLM+ls0df5axxoJzZxUy8WVZDLnrf/DSh4mS5yYj0BDD1Hvl2RY
qAWZg+q9rwZ2Tqwnp2W9SotwV11aypzVdU9WEt2KoMdsSI+atGanMx+aPwUJT4B8
lC17o/9ohTPDTi3uQJNTW7AwJMbOdNgJOZvvgghi1MkBxU/rHH3fau9gWov6T82i
uWL/0jLfq/xhgYJ26Os5SP2j4puO98ayiTXDKAVRFmp7FTlVdRFPruaB6Rd3WPhZ
04n6uqa/B8OuHhv1gxabQdLgwOgujpaFpmHyoj0BF5Ho
-----END CERTIFICATE-----"""

right_certificate_chain = """-----BEGIN CERTIFICATE-----
MIIGrTCCBZWgAwIBAgIMAxuwBcg57I1h4JOEMA0GCSqGSIb3DQEBCwUAMFAxCzAJ
BgNVBAYTAkJFMRkwFwYDVQQKExBHbG9iYWxTaWduIG52LXNhMSYwJAYDVQQDEx1H
bG9iYWxTaWduIFJTQSBPViBTU0wgQ0EgMjAxODAeFw0yNDA1MDYwMzE3MTdaFw0y
NTA2MDcwMzE3MTZaMH4xCzAJBgNVBAYTAkNOMRIwEAYDVQQIDAnmtZnmsZ/nnIEx
EjAQBgNVBAcMCeWugeazouW4gjEtMCsGA1UECgwk5rWZ5rGf5p6B5rCq5pm66IO9
56eR5oqA5pyJ6ZmQ5YWs5Y+4MRgwFgYDVQQDDA8qLnplZWtybGlmZS5jb20wggEi
MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCglDA0tnCPqgzUgP51IPu01Xs3
a3pgKYhjglGzORtAP41WLpy+ve0EhLxllZrQkMCcsz+eWCA/oxH0iSlyFi78cTxA
EQgJ02kBIjIopzxJaWGefjadItPqRqMTTpEHX0nxp+3lOim78YrE3IKcUQbxNT2C
q7dx5yMsD6g8i2VyLaw7JkweIlVeCkfUTLqIskrG3S/MLqK7UE2KrqD/QeIWayFc
UxrrF3ETiJkn+YUA2ZTuQ/01wLokVAC9Ysc87BvSXhr5UMFEGJUhY/HJXkv3V8ML
2aEWdOGrSYUNKVd+4vKnJuXYIJLcN7ZikqeOpM/0+V5kQQSankgVxmHvwxB1AgMB
AAGjggNXMIIDUzAOBgNVHQ8BAf8EBAMCBaAwDAYDVR0TAQH/BAIwADCBjgYIKwYB
BQUHAQEEgYEwfzBEBggrBgEFBQcwAoY4aHR0cDovL3NlY3VyZS5nbG9iYWxzaWdu
LmNvbS9jYWNlcnQvZ3Nyc2FvdnNzbGNhMjAxOC5jcnQwNwYIKwYBBQUHMAGGK2h0
dHA6Ly9vY3NwLmdsb2JhbHNpZ24uY29tL2dzcnNhb3Zzc2xjYTIwMTgwVgYDVR0g
BE8wTTBBBgkrBgEEAaAyARQwNDAyBggrBgEFBQcCARYmaHR0cHM6Ly93d3cuZ2xv
YmFsc2lnbi5jb20vcmVwb3NpdG9yeS8wCAYGZ4EMAQICMD8GA1UdHwQ4MDYwNKAy
oDCGLmh0dHA6Ly9jcmwuZ2xvYmFsc2lnbi5jb20vZ3Nyc2FvdnNzbGNhMjAxOC5j
cmwwKQYDVR0RBCIwIIIPKi56ZWVrcmxpZmUuY29tgg16ZWVrcmxpZmUuY29tMB0G
A1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjAfBgNVHSMEGDAWgBT473/yzXhn
qN5vjySNiPGHAwKz6zAdBgNVHQ4EFgQUWNyNg+4HOZZxKYxh/Vz+MS7fIh0wggF9
BgorBgEEAdZ5AgQCBIIBbQSCAWkBZwB1AKLjCuRF772tm3447Udnd1PXgluElNcr
XhssxLlQpEfnAAABj0vn5jcAAAQDAEYwRAIgJIn6bk7wipY+5Z5+SYfaxmOrgE1B
uMsLQW7L8JKPsXYCIDN57d9gJFsy+VkqdqEAVY69uQWtxJVzzAI+J7atLb71AHUA
TnWjJ1yaEMM4W2zU3z9S6x3w4I4bjWnAsfpksWKaOd8AAAGPS+fnSwAABAMARjBE
AiBNswzZVDrAP4D2VLbocXE9JsJb2bJpiptrF+bMrjGLuwIgaBGClOR6nEwcvhIu
8voz1q8Q6bEgMBQXW2B88IyG9p0AdwDgkrP8DB3I52g2H95huZZNClJ4GYpy1nLE
sE2lbW9UBAAAAY9L5+dfAAAEAwBIMEYCIQDT3R7jguKkZkUqtPlwyzxnmmloQkjp
PAgGP2QdVKNm8wIhALP9JnI9Q2wiA2154REakvaqBDV0uy/2W5AVmXG6GOO2MA0G
CSqGSIb3DQEBCwUAA4IBAQCUj6Yer+WJiNXSIu7zTRtIDp6CW18IEvEnYx/H2Gqp
EEMrCBECxzzksyLM+ls0df5axxoJzZxUy8WVZDLnrf/DSh4mS5yYj0BDD1Hvl2RY
qAWZg+q9rwZ2Tqwnp2W9SotwV11aypzVdU9WEt2KoMdsSI+atGanMx+aPwUJT4B8
lC17o/9ohTPDTi3uQJNTW7AwJMbOdNgJOZvvgghi1MkBxU/rHH3fau9gWov6T82i
uWL/0jLfq/xhgYJ26Os5SP2j4puO98ayiTXDKAVRFmp7FTlVdRFPruaB6Rd3WPhZ
04n6uqa/B8OuHhv1gxabQdLgwOgujpaFpmHyoj0BF5Ho
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIETjCCAzagAwIBAgINAe5fIh38YjvUMzqFVzANBgkqhkiG9w0BAQsFADBMMSAw
HgYDVQQLExdHbG9iYWxTaWduIFJvb3QgQ0EgLSBSMzETMBEGA1UEChMKR2xvYmFs
U2lnbjETMBEGA1UEAxMKR2xvYmFsU2lnbjAeFw0xODExMjEwMDAwMDBaFw0yODEx
MjEwMDAwMDBaMFAxCzAJBgNVBAYTAkJFMRkwFwYDVQQKExBHbG9iYWxTaWduIG52
LXNhMSYwJAYDVQQDEx1HbG9iYWxTaWduIFJTQSBPViBTU0wgQ0EgMjAxODCCASIw
DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKdaydUMGCEAI9WXD+uu3Vxoa2uP
UGATeoHLl+6OimGUSyZ59gSnKvuk2la77qCk8HuKf1UfR5NhDW5xUTolJAgvjOH3
idaSz6+zpz8w7bXfIa7+9UQX/dhj2S/TgVprX9NHsKzyqzskeU8fxy7quRU6fBhM
abO1IFkJXinDY+YuRluqlJBJDrnw9UqhCS98NE3QvADFBlV5Bs6i0BDxSEPouVq1
lVW9MdIbPYa+oewNEtssmSStR8JvA+Z6cLVwzM0nLKWMjsIYPJLJLnNvBhBWk0Cq
o8VS++XFBdZpaFwGue5RieGKDkFNm5KQConpFmvv73W+eka440eKHRwup08CAwEA
AaOCASkwggElMA4GA1UdDwEB/wQEAwIBhjASBgNVHRMBAf8ECDAGAQH/AgEAMB0G
A1UdDgQWBBT473/yzXhnqN5vjySNiPGHAwKz6zAfBgNVHSMEGDAWgBSP8Et/qC5F
JK5NUPpjmove4t0bvDA+BggrBgEFBQcBAQQyMDAwLgYIKwYBBQUHMAGGImh0dHA6
Ly9vY3NwMi5nbG9iYWxzaWduLmNvbS9yb290cjMwNgYDVR0fBC8wLTAroCmgJ4Yl
aHR0cDovL2NybC5nbG9iYWxzaWduLmNvbS9yb290LXIzLmNybDBHBgNVHSAEQDA+
MDwGBFUdIAAwNDAyBggrBgEFBQcCARYmaHR0cHM6Ly93d3cuZ2xvYmFsc2lnbi5j
b20vcmVwb3NpdG9yeS8wDQYJKoZIhvcNAQELBQADggEBAJmQyC1fQorUC2bbmANz
EdSIhlIoU4r7rd/9c446ZwTbw1MUcBQJfMPg+NccmBqixD7b6QDjynCy8SIwIVbb
0615XoFYC20UgDX1b10d65pHBf9ZjQCxQNqQmJYaumxtf4z1s4DfjGRzNpZ5eWl0
6r/4ngGPoJVpjemEuunl1Ig423g7mNA2eymw0lIYkN5SQwCuaifIFJ6GlazhgDEw
fpolu4usBCOmmQDo8dIm7A9+O4orkjgTHY+GzYZSR+Y0fFukAj6KYXwidlNalFMz
hriSqHKvoflShx8xpfywgVcvzfTO3PYkz6fiNJBonf6q8amaEsybwMbDqKWwIX7e
SPY=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIETjCCAzagAwIBAgINAe5fFp3/lzUrZGXWajANBgkqhkiG9w0BAQsFADBXMQsw
CQYDVQQGEwJCRTEZMBcGA1UEChMQR2xvYmFsU2lnbiBudi1zYTEQMA4GA1UECxMH
Um9vdCBDQTEbMBkGA1UEAxMSR2xvYmFsU2lnbiBSb290IENBMB4XDTE4MDkxOTAw
MDAwMFoXDTI4MDEyODEyMDAwMFowTDEgMB4GA1UECxMXR2xvYmFsU2lnbiBSb290
IENBIC0gUjMxEzARBgNVBAoTCkdsb2JhbFNpZ24xEzARBgNVBAMTCkdsb2JhbFNp
Z24wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDMJXaQeQZ4Ihb1wIO2
hMoonv0FdhHFrYhy/EYCQ8eyip0EXyTLLkvhYIJG4VKrDIFHcGzdZNHr9SyjD4I9
DCuul9e2FIYQebs7E4B3jAjhSdJqYi8fXvqWaN+JJ5U4nwbXPsnLJlkNc96wyOkm
DoMVxu9bi9IEYMpJpij2aTv2y8gokeWdimFXN6x0FNx04Druci8unPvQu7/1PQDh
BjPogiuuU6Y6FnOM3UEOIDrAtKeh6bJPkC4yYOlXy7kEkmho5TgmYHWyn3f/kRTv
riBJ/K1AFUjRAjFhGV64l++td7dkmnq/X8ET75ti+w1s4FRpFqkD2m7pg5NxdsZp
hYIXAgMBAAGjggEiMIIBHjAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB
/zAdBgNVHQ4EFgQUj/BLf6guRSSuTVD6Y5qL3uLdG7wwHwYDVR0jBBgwFoAUYHtm
GkUNl8qJUC99BM00qP/8/UswPQYIKwYBBQUHAQEEMTAvMC0GCCsGAQUFBzABhiFo
dHRwOi8vb2NzcC5nbG9iYWxzaWduLmNvbS9yb290cjEwMwYDVR0fBCwwKjAooCag
JIYiaHR0cDovL2NybC5nbG9iYWxzaWduLmNvbS9yb290LmNybDBHBgNVHSAEQDA+
MDwGBFUdIAAwNDAyBggrBgEFBQcCARYmaHR0cHM6Ly93d3cuZ2xvYmFsc2lnbi5j
b20vcmVwb3NpdG9yeS8wDQYJKoZIhvcNAQELBQADggEBACNw6c/ivvVZrpRCb8RD
M6rNPzq5ZBfyYgZLSPFAiAYXof6r0V88xjPy847dHx0+zBpgmYILrMf8fpqHKqV9
D6ZX7qw7aoXW3r1AY/itpsiIsBL89kHfDwmXHjjqU5++BfQ+6tOfUBJ2vgmLwgtI
fR4uUfaNU9OrH0Abio7tfftPeVZwXwzTjhuzp3ANNyuXlava4BJrHEDOxcd+7cJi
WOx37XMiwor1hkOIreoTbv3Y/kIvuX1erRjvlJDKPSerJpSZdcfL03v3ykzTr1Eh
kluEfSufFT90y1HonoMOFm8b50bOI7355KKL0jlrqnkckSziYSQtjipIcJDEHsXo
4HA=
-----END CERTIFICATE-----"""

right_privateKey = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAoJQwNLZwj6oM1ID+dSD7tNV7N2t6YCmIY4JRszkbQD+NVi6c
vr3tBIS8ZZWa0JDAnLM/nlggP6MR9IkpchYu/HE8QBEICdNpASIyKKc8SWlhnn42
nSLT6kajE06RB19J8aft5Topu/GKxNyCnFEG8TU9gqu3cecjLA+oPItlci2sOyZM
HiJVXgpH1Ey6iLJKxt0vzC6iu1BNiq6g/0HiFmshXFMa6xdxE4iZJ/mFANmU7kP9
NcC6JFQAvWLHPOwb0l4a+VDBRBiVIWPxyV5L91fDC9mhFnThq0mFDSlXfuLypybl
2CCS3De2YpKnjqTP9PleZEEEmp5IFcZh78MQdQIDAQABAoIBAAuJulD/TuUzvcpD
HoWCAjQDJuBbi6Z/NXqY8Y/kKY4bQuePX9ngwbgSZYsTDdWwoPZhds/E20RXTkH4
3Q6Cg4vGAyNDVgWGuEPJljsPkShhNw9xWDFAQGPUAYGwooEaGrEPdOuEm10SxPrS
MVxUAiCwx6Os/PhlOETBN0Bqb7adbkwAJ24Fjms7trnnOHsjAhBZO/1cJrh/QcGE
VHqkqZl0jrIGHQPje7Azg+OMzjzwKWnxaqWtT91jrNPbyTki2LaA/I0Wg517/ZZl
XJ/muOSdIPle7Oi5c2IiZ1AIjreqcrm3ZFuolvFRkRybByPZ/wvo0Eo5saLCAxdw
begW2iECgYEA2mfdcp/D9/iZGA86hqoVUtJcE053yFCOJx6fhHZKMlV5FLs2i95F
6vcPvWyS04+3YFC3NDuH8hd5+WIAlj7s439c/9Z+kp373nDIydT2HDhWDl24NY3O
yA+r5IzXTceh06TUy2cnu4rQnqkIpvC++h5MQMm8UgjoIxFHmQzOoT0CgYEAvDgo
3DPIMAOGf95oWUCowTDw3YFZV77AgWKmPlnThXO9eJ51R1gH9xjDqISCl+egF+fS
A0Ai1+LoXnkyLvwlEMhWkC15CpsLGIYmi1FZvKOpD37I9GMQUkcXYMNNz6SZOU/y
M4AWi6X3IkMShjIWK6FMZCp5nWWkNnGhO5D8r5kCgYAyY2Qj3dhIjYJEmr7V8seY
pA+6JJBeFre1Lst+tAvKMQ4OSmL7Qfy/iOCIw1Pcm3ujLPwXgOSMZf4uGv4nq7zb
f7blD4eELA6/8yVf61IckKLKDbVCJcVfQr5VrGi/+R7MxWqSwunXyt72u+jTGxf0
fKj7CY/5HTTxYjsyhFHnwQKBgEIv5X553x2zP6rbhQpNyIoXMbxS7h4DACL/k8I9
SDqXlrtBzbAG7tYfqT4rStksJIoDhUCLXzVXn6sJJ3KKTGZ4bKhKtVPbba10Dz3S
n6HMU3kVdokqBOVKBpiKVWR9VzxmNp+RnVwCQsOTnoH+PvmcwQZAQX/t7C8RCkeu
Fo2RAoGAcAo6/vOzEJKKrG9+l0PcxVdlJI3MLVyCmmM1/V3IO5+uEgk95fHmbiL8
0XNiORuJYurAOHTuLOyxpI8DuGyt/bG3lZfUYk+m0kSIcP4VoK6yVioVvp571LqM
CAIp+aubJC7sxfVhykHSx8ChUtaVMW8NZ6cFzksCiOfTV+6ykvs=
-----END RSA PRIVATE KEY-----"""

bucket_name = "test-union-sdk-cname"
right_domain_name = 'customdomain.zeekrlife.com'
right_name = 'aaa'
right_certificate_id = '1234512345123450'
right_certificate_info = CustomDomainConfiguration(name=right_name, certificateId=right_certificate_id,
                                                   certificate=right_certificate,
                                                   certificateChain=right_certificate_chain,
                                                   privateKey=right_privateKey)


class TestCustomDomain(object):

    def get_client(self):

        path_style = True if test_config["auth_type"] == "v2" else False
        obsClient = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style,
        )

        return obsClient

    def delete_bucket(self, obs_clinet, bucket_name):
        del_resp = obs_clinet.deleteBucket(bucket_name)
        assert del_resp.status == 204

    def delete_custom_domain(self, obs_clinet, bucket_name, domain_name):
        del_resp = obs_clinet.deleteBucketCustomDomain(bucket_name, domain_name)
        assert del_resp.status == 204

    def get_string_by_length(self, length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def test_put_custom_domain_certificate_name(self):
        obs_client = self.get_client()
        no_name_certificate_info = CustomDomainConfiguration(name=None, certificate=right_certificate,
                                                             certificateChain=right_certificate_chain,
                                                             privateKey=right_privateKey)
        wrong_len_certificate_info = CustomDomainConfiguration(name='aa', certificate=right_certificate,
                                                               certificateChain=right_certificate_chain,
                                                               privateKey=right_privateKey)
        longer_name = self.get_string_by_length(64)
        wrong_len_certificate_info2 = CustomDomainConfiguration(name=longer_name, certificate=right_certificate,
                                                                certificateChain=right_certificate_chain,
                                                                privateKey=right_privateKey)
        # 证书配置不带Name
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, no_name_certificate_info)
        assert str(exc_info.value) == "Certificate Name does not exist."
        # 证书配置Name长度过短
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, wrong_len_certificate_info)
        assert str(exc_info.value) == "Certificate Name length must be between 3 and 63 characters. (value len: 2)"
        # 证书配置Name长度过长
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, wrong_len_certificate_info2)
        assert str(exc_info.value) == "Certificate Name length must be between 3 and 63 characters. (value len: 64)"
        # Name参数正常
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 200

        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)

    def test_put_custom_domain_certificate_Id(self):
        obs_client = self.get_client()
        certificate_info_without_id = CustomDomainConfiguration(name=right_name, certificate=right_certificate,
                                                                certificateChain=right_certificate_chain,
                                                                privateKey=right_privateKey)
        certificate_info_with_wrong_len_id = CustomDomainConfiguration(name=right_name,
                                                                       certificateId='123456789012345',
                                                                       certificate=right_certificate,
                                                                       certificateChain=right_certificate_chain,
                                                                       privateKey=right_privateKey)
        # 证书配置不带CertificateId
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_without_id)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)
        # 证书配置带CertificateId
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)

        # 证书配置带CertificateId,长度为15
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_with_wrong_len_id)
        assert str(exc_info.value) == "CertificateId length must be between 16 and 16 characters. (value len: 15)"

    def test_put_custom_domain_certificate(self):
        obs_client = self.get_client()
        certificate_info_without_certificate = CustomDomainConfiguration(name=right_name,
                                                                         certificateId=right_certificate_id,
                                                                         certificateChain=right_certificate_chain,
                                                                         privateKey=right_privateKey)
        certificate_info_with_wrong_len_cert = CustomDomainConfiguration(name=right_name,
                                                                         certificateId=right_certificate_id,
                                                                         certificate=self.get_string_by_length(
                                                                             40 * 1024),
                                                                         certificateChain=right_certificate_chain,
                                                                         privateKey=right_privateKey)
        # 证书配置不带Certificate
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_without_certificate)
        assert str(exc_info.value) == "Certificate does not exist."
        # 证书配置带正确Certificate
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)

        # 证书配置带Certificate, 长度为40k
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_with_wrong_len_cert)
        assert str(
            exc_info.value) == "set bucket custom domain failed, reason: XML body size exceeds 40 KB limit, size: 48361"

    def test_put_custom_domain_certificate_chain(self):
        obs_client = self.get_client()
        certificate_info_without_certificate_chain = CustomDomainConfiguration(name=right_name,
                                                                               certificateId=right_certificate_id,
                                                                               certificate=right_certificate,
                                                                               privateKey=right_privateKey)
        certificate_info_with_wrong_len_cert_chain = CustomDomainConfiguration(name=right_name,
                                                                               certificateId=right_certificate_id,
                                                                               certificate=right_certificate,
                                                                               certificateChain=
                                                                               self.get_string_by_length(40 * 1024),
                                                                               privateKey=right_privateKey)
        # 证书配置不带CertificateChain
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name,
                                                      certificate_info_without_certificate_chain)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)
        # 证书配置带正确CertificateChain
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)
        # 证书配置带CertificateChain,长度为40k
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_with_wrong_len_cert_chain)
        assert str(
            exc_info.value) == "set bucket custom domain failed, reason: XML body size exceeds 40 KB limit, size: 45253"

    def test_put_custom_domain_certificate_privateKey(self):
        obs_client = self.get_client()
        certificate_info_without_key = CustomDomainConfiguration(name=right_name,
                                                                 certificateId=right_certificate_id,
                                                                 certificate=right_certificate,
                                                                 certificateChain=right_certificate_chain)
        certificate_info_with_wrong_len_key = CustomDomainConfiguration(name=right_name,
                                                                        certificateId=right_certificate_id,
                                                                        certificate=right_certificate,
                                                                        certificateChain=right_certificate_chain,
                                                                        privateKey=self.get_string_by_length(40 * 1024))
        # 证书配置不带privateKey
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_without_key)
        assert str(exc_info.value) == "PrivateKey does not exist."
        # 证书配置带正确privateKey
        set_result = obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, right_domain_name)
        # 证书配置带privateKey,长度40k
        with pytest.raises(Exception) as exc_info:
            obs_client.setBucketCustomDomain(bucket_name, right_domain_name, certificate_info_with_wrong_len_key)
        assert str(
            exc_info.value) == "set bucket custom domain failed, reason: XML body size exceeds 40 KB limit, size: 49060"

    def test_put_custom_domain_certificate_safety(self):
        safe_obs_client = self.get_client()
        unsafe_endpoint = 'http://' + test_config["endpoint"]
        path_style = True if test_config["auth_type"] == "v2" else False
        unsafe_obs_client = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=unsafe_endpoint,
            is_signature_negotiation=False,
            path_style=path_style,
        )
        # 不带证书，通过http方式访问
        set_result = unsafe_obs_client.setBucketCustomDomain(bucket_name, right_domain_name)
        assert set_result.status == 200
        self.delete_custom_domain(unsafe_obs_client, bucket_name, right_domain_name)
        # 不带证书通过https方式访问
        set_result = safe_obs_client.setBucketCustomDomain(bucket_name, right_domain_name)
        assert set_result.status == 200
        self.delete_custom_domain(safe_obs_client, bucket_name, right_domain_name)
        # 带证书，通过http方式访问
        set_result = unsafe_obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 400
        # 带证书，通过https方式访问
        set_result = safe_obs_client.setBucketCustomDomain(bucket_name, right_domain_name, right_certificate_info)
        assert set_result.status == 200
        self.delete_custom_domain(safe_obs_client, bucket_name, right_domain_name)

    def test_put_get_custom_domain_certificate(self):
        obs_client = self.get_client()
        # 设置自定义域名配置a域名，无证书
        domain_name_a = 'aaa.zeekrlife.com'
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_a)
        assert set_result.status == 200
        # 设置自定义域名配置b域名，有证书
        domain_name_b = 'bbb.zeekrlife.com'
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_b, right_certificate_info)
        assert set_result.status == 200
        # 设置自定义域名配置c域名，有证书
        domain_name_c = 'ccc.zeekrlife.com'
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_c, right_certificate_info)
        assert set_result.status == 200
        # 设置自定义域名配置a域名，带证书，name为aaa
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_a, right_certificate_info)
        assert set_result.status == 200
        self.delete_custom_domain(obs_client, bucket_name, domain_name_a)
        # 设置自定义域名配置b域名，带新证书，获取b域名对应证书id，对比2中设置的证书id。
        new_certificate_info = CustomDomainConfiguration(name=right_name, certificateId='1234567980123456',
                                                         certificate=right_certificate,
                                                         certificateChain=right_certificate_chain,
                                                         privateKey=right_privateKey)
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_b, new_certificate_info)
        assert set_result.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name_b:
                assert domain.certificate_id == '1234567980123456'
        self.delete_custom_domain(obs_client, bucket_name, domain_name_b)

        # 设置自定义域名配置c域名，不带证书，获取c域名对应证书id
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_c)
        assert set_result.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name_c:
                assert not domain.certificate_id
        self.delete_custom_domain(obs_client, bucket_name, domain_name_c)
        # 设置自定义域名配置a域名，带新证书，name为bbb，获取a域名对应证书id
        new_certificate_info2 = CustomDomainConfiguration(name='bbb', certificateId='1234567980123456',
                                                          certificate=right_certificate,
                                                          certificateChain=right_certificate_chain,
                                                          privateKey=right_privateKey)
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_a, new_certificate_info2)
        assert set_result.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name_a:
                assert domain.certificate_id == '1234567980123456'
        self.delete_custom_domain(obs_client, bucket_name, domain_name_a)

    def test_put_get_delete_custom_domain_certificate(self):
        obs_client = self.get_client()
        # 设置自定义域名配置a域名，无证书
        domain_name_a = 'aaa.zeekrlife.com'
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_a)
        assert set_result.status == 200
        # 设置自定义域名配置b域名，有证书
        domain_name_b = 'bbb.zeekrlife.com'
        set_result = obs_client.setBucketCustomDomain(bucket_name, domain_name_b, right_certificate_info)
        assert set_result.status == 200
        # 获取自定义域名列表，检查a、b域名是否在结果中，检查证书id
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name_a:
                assert not domain.certificate_id
            elif domain.domain_name == domain_name_b:
                assert domain.certificate_id == right_certificate_id
        # 删除自定义域名a
        del_resp = obs_client.deleteBucketCustomDomain(bucket_name, domain_name_a)
        assert del_resp.status == 204
        # 获取自定义域名列表，a域名不在返回的列表中，b域名在返回的列表中
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        is_a_exist = False
        is_b_exist = False
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name_a:
                is_a_exist = True
            elif domain.domain_name == domain_name_b:
                is_b_exist = True
        assert is_a_exist is False
        assert is_b_exist is True
        self.delete_custom_domain(obs_client, bucket_name, domain_name_b)