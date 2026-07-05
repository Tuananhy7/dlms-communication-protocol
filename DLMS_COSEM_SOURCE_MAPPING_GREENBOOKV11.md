# DLMS/COSEM Source Mapping

Source note: `C:\Users\Admin\Downloads\dlms_cosem_notes.md`

Mapped source root: `GuruxDLMSServerExample2/dlms/`

This document maps the DLMS/COSEM concepts from the note to the Gurux C source tree. Line numbers are from the current local checkout.

## Quick Mental Model

The `dlms/` folder is the reusable Gurux DLMS/COSEM protocol library. The application-specific meter behavior lives mostly in `GuruxDLMSServerExample2/src/main.c`.

Core source flow:

```text
Physical/profile bytes
  -> dlms.c frame parsing: HDLC, WRAPPER, PLC, M-Bus, TCP
  -> server.c or client.c service dispatch
  -> apdu.c association / xDLMS negotiation
  -> gxget.c, gxset.c, gxinvoke.c COSEM data access
  -> gxobjects.c / cosem.c object and datatype helpers
  -> ciphering.c / gxaes.c / gxecdsa.c security
```

## Source Tree Map

```text
GuruxDLMSServerExample2/dlms/
  include/    Public headers for the Gurux DLMS library.
  src/        C implementations.
```

Important source groups:

| Area | Main files | Role |
|---|---|---|
| Application association / ACSE / xDLMS APDU | `src/apdu.c`, `include/apdu.h` | AARQ/AARE, application context, user information, authentication fields, conformance negotiation |
| Server-side service dispatcher | `src/server.c`, `include/server.h`, `src/serverevents.c` | Handles incoming server requests and maps commands to GET/SET/ACTION/read/write/release handlers |
| Client-side service builder/parser | `src/client.c`, `include/client.h` | Builds client requests and parses responses |
| Frame/profile layer and PDU assembly | `src/dlms.c`, `include/dlms.h` | HDLC, WRAPPER/TCP, PLC, M-Bus frame parsing, block transfer, PDU creation |
| COSEM data GET | `src/gxget.c`, `include/gxget.h` | Encodes object attributes for reads |
| COSEM data SET | `src/gxset.c`, `include/gxset.h` | Applies writes to object attributes |
| COSEM ACTION/method | `src/gxinvoke.c`, `include/gxinvoke.h` | Invokes object methods |
| COSEM object model | `src/gxobjects.c`, `src/cosem.c`, `include/gxobjects.h`, `include/cosem.h` | Object lifecycle, attribute counts, method counts, LN lookup, datatype encode/decode |
| Security | `src/ciphering.c`, `src/gxaes.c`, `src/gxecdsa.c`, `src/gxkey.c` | AES-GCM-like ciphering, keys, ECDSA signing/verify |
| Notifications / push | `src/notify.c`, `include/notify.h` | DataNotification, EventNotification, PushSetup messages |
| Message containers | `src/message.c`, `src/replydata.c`, `src/parameters.c` | Packet lists, reply state, LN/SN parameter containers |
| Serialization | `src/gxserializer.c`, `include/gxserializer.h` | Save/load COSEM object state |
| Data buffers and variant values | `src/bytebuffer.c`, `src/variant.c`, `src/objectarray.c`, `src/gxarray.c` | Dynamic/static container utilities used everywhere |

## Section 9 Mapping: Application Layer

### ASO Structure

| Concept from note | Source mapping | Code block / functions |
|---|---|---|
| ACSE association control | `src/apdu.c`, `src/server.c`, `src/client.c` | `apdu_generateAarq` line 1351, `apdu_generateAARE` line 2140, `svr_HandleAarqRequest` line 375, `cl_aarqRequest` line 282, `cl_parseAAREResponse` line 380 |
| xDLMS ASE data transfer | `src/server.c`, `src/client.c`, `src/dlms.c` | Server handlers: `svr_handleGetRequest`, `svr_handleSetRequest`, `svr_handleMethodRequest`; client builders: `cl_read`, `cl_write`, `cl_method`; PDU builders: `dlms_getLNPdu`, `dlms_getSNPdu` |
| Control Function (CF) coordination | `src/server.c`, `src/dlms.c` | `svr_handleCommand` line 3415 dispatches DLMS commands; `dlms_getPdu` line 5216 builds outgoing APDUs |
| Client SN Mapper ASE | `src/server.c`, `src/client.c`, `src/dlms.c` | `svr_findSNObject` line 2126, `svr_handleReadRequest` line 2536, `svr_handleWriteRequest` line 2628, `cl_readSN` line 784, `cl_writeSN` line 1929, `dlms_getSNPdu` line 5618 |

### Association Management

| Service | Server-side mapping | Client-side mapping | Notes |
|---|---|---|---|
| `COSEM-OPEN` | `svr_HandleAarqRequest` line 375 | `cl_aarqRequest` line 282, `cl_parseAAREResponse` line 380 | Uses APDU AARQ/AARE encode/decode in `apdu.c`. |
| `COSEM-RELEASE` | `svr_handleReleaseRequest` line 3138 | `cl_releaseRequest` line 1422, `cl_releaseRequest2` line 1432 | Handles association release. |
| `COSEM-ABORT` | `svr_handleCommand` line 3415 | Search command dispatch around abort command handling | Abort handling is command-dispatch level, not a standalone obvious `abort` function in this checkout. |
| HDLC link setup before AA | `svr_handleSnrmRequest` line 671 | `cl_snrmRequest` line 58, `cl_parseUAResponse` line 178 | SNRM/UA belongs to the 3-layer HDLC profile. |

Primary APDU functions:

```text
apdu.c
  46    apdu_getAuthenticationString
  118   apdu_generateApplicationContextName
  243   apdu_getInitiateRequest
  315   apdu_generateUserInformation
  396   apdu_parseUserInformation
  745   apdu_verifyUserInformation
  981   apdu_parseApplicationContextName
  1094  apdu_validateAare
  1125  apdu_updatePassword
  1172  apdu_updateAuthentication
  1263  apdu_getUserInformation
  1351  apdu_generateAarq
  1437  apdu_parsePDU
  2140  apdu_generateAARE
```

### LN Data Access: GET, SET, ACTION, ACCESS

| Service | Main server path | COSEM object path | Client path |
|---|---|---|---|
| `GET` | `server.c:1523 svr_getRequestNormal`, `server.c:1738 svr_getRequestNextDataBlock`, `server.c:1834 svr_getRequestWithList`, `server.c:2054 svr_handleGetRequest` | `gxget.c:5550 cosem_getValue` dispatches object attribute encoding | `client.c:821 cl_readLN`, `client.c:997 cl_read`, `client.c:1301 cl_getData` |
| `SET` | `server.c:919 svr_handleSetRequest2`, `server.c:1185 svr_handleSetRequestWithList`, `server.c:1314 svr_hanleSetRequestWithDataBlock`, `server.c:1454 svr_handleSetRequest` | `gxset.c:46 cosem_setValue` | `client.c:1603 cl_write`, `client.c:1644 cl_writeList`, `client.c:1850 cl_writeLN` |
| `ACTION` | `server.c:2880 svr_handleMethodRequest`, `server.c:4355 svr_invoke` | `gxinvoke.c:4126 cosem_invoke` dispatches object method invocation | `client.c:1969 cl_method`, `client.c:2016 cl_methodLN`, `client.c:2107 cl_methodLN2` |
| `ACCESS` | Search command dispatch in `server.c:3415 svr_handleCommand` | Uses common GET/SET/action support blocks | Search `DLMS_COMMAND_ACCESS` in `server.c`, `client.c`, `dlms.c` if expanding ACCESS behavior |

Common GET code block:

```text
server.c
  svr_handleCommand
    -> svr_handleGetRequest
       -> svr_getRequestNormal / svr_getRequestWithList / svr_getRequestNextDataBlock
          -> gxget.c:cosem_getValue
```

Common SET code block:

```text
server.c
  svr_handleCommand
    -> svr_handleSetRequest
       -> svr_handleSetRequest2 / svr_handleSetRequestWithList / svr_hanleSetRequestWithDataBlock
          -> gxset.c:cosem_setValue
```

Common ACTION code block:

```text
server.c
  svr_handleCommand
    -> svr_handleMethodRequest
       -> svr_invoke
          -> gxinvoke.c:cosem_invoke
```

### SN Data Access: Read, Write, UnconfirmedWrite

| Service | Source mapping | Functions |
|---|---|---|
| SN Read | `server.c`, `client.c`, `dlms.c` | `svr_handleReadRequest` line 2536, `svr_handleRead` line 2173, `svr_getReadData` line 2243, `cl_readSN` line 784, `dlms_getSNPdu` line 5618 |
| SN Write | `server.c`, `client.c` | `svr_handleWriteRequest` line 2628, `cl_writeSN` line 1929 |
| UnconfirmedWrite | `server.c` command dispatch | Search `UNCONFIRMED_WRITE` in `server.c` and command enum definitions in `include/enums.h` |

### Unsolicited Data Push Services

| Service | Source mapping | Functions |
|---|---|---|
| `DataNotification` | `src/notify.c`, `src/dlms.c` | `notify_generateDataNotificationMessages2` line 88, `notify_generateDataNotificationMessages` line 119, `dlms_handleDataNotification` line 4734 |
| `EventNotification` | `src/notify.c` | `notify_generateEventNotificationMessages` line 164, `notify_generateEventNotificationMessages2` line 219 |
| Push setup | `src/notify.c`, `src/gxget.c` | `notify_generatePushSetupMessages` line 251, `notify_parsePush` line 382, `notify_getPushValues` line 485, `cosem_getPushSetup` line 4754 |
| `InformationReport` | `src/dlms.c`, command dispatch | Search `INFORMATION_REPORT` in `dlms.c`, `server.c`, and `include/enums.h` |

Notify code block:

```text
notify.c
  notify_addData
  notify_generateDataNotificationMessages
  notify_generateEventNotificationMessages
  notify_generatePushSetupMessages
  notify_parsePush
```

## Information Security Mapping

### Authentication

| Level | Source mapping | Functions / blocks |
|---|---|---|
| No security | `apdu.c`, `dlmsSettings.c`, `server.c` | Authentication enum values are applied through APDU negotiation and settings. |
| Low-Level Security (LLS) | `apdu.c`, application `main.c` | `apdu_getAuthenticationString`, `apdu_updatePassword`, `apdu_updateAuthentication`; app validates password in server callback. |
| High-Level Security (HLS) | `apdu.c`, `ciphering.c`, `gxecdsa.c`, `server.c` | `apdu_updateAuthentication`, `dlms_generateChallenge` line 6501, `dlms_secure` line 6632, `gxecdsa_sign`, `gxecdsa_verify` |

Security-related APDU block:

```text
apdu.c
  apdu_getAuthenticationString
  apdu_updatePassword
  apdu_updateAuthentication
  apdu_generateAarq
  apdu_generateAARE
```

### Cryptography

| Mechanism | Source mapping | Functions |
|---|---|---|
| AES-GCM / authenticated encryption | `src/ciphering.c`, `src/gxaes.c` | `cip_init`, `cip_clear`, `cip_crypt`, `cip_encrypt`, `cip_decrypt`, `cip_encryptKey`, `cip_decryptKey`; internal `gxgcm_*` helpers |
| ECDSA | `src/gxecdsa.c`, `src/privateKey.c`, `src/publicKey.c`, `src/curve.c`, `src/eccPoint.c`, `src/shamirs.c`, `src/bigInteger.c` | `gxecdsa_verify` line 76, `gxecdsa_sign` line 148, `gxecdsa_generateKeyPair` line 229 |
| Keys | `src/gxkey.c`, `src/ciphering.c` | `key_init`, `key_init2`, `key_init3`, cipher key buffers in `ciphering` settings |

Cipher block:

```text
ciphering.c
  gxgcm_init
  gxgcm_transformBlock
  gxgcm_getTag
  cip_crypt
  cip_encrypt
  cip_decrypt
```

## Additional Mechanisms

### General Block Transfer (GBT) And Blocked Data

| Concept | Source mapping | Functions |
|---|---|---|
| General Block Transfer | `src/dlms.c` | `dlms_handleGbt` line 4808 |
| GET next data block | `src/server.c` | `svr_getRequestNextDataBlock` line 1738 |
| SET with data block | `src/server.c` | `svr_hanleSetRequestWithDataBlock` line 1314 |
| SN read data block | `src/server.c` | `svr_handleReadBlockNumberAccess` line 2321, `svr_handleReadDataBlockAccess` line 2418 |
| Client receiver ready | `src/client.c`, `src/dlms.c` | `cl_receiverReady` line 1412, `dlms_receiverReady` line 3773 |
| Multiple blocks | `src/dlms.c` | `dlms_appendMultipleSNBlocks` line 5561, `dlms_multipleBlocks` line 5796 |

### Data Compression

The note mentions V.44 compression. In this checkout, there is no obvious dedicated `v44` or compression module under `dlms/src`. Treat compression support as absent or not compiled in until confirmed by searching the exact target branch.

Recommended search:

```powershell
Select-String -Path GuruxDLMSServerExample2/dlms/src/*.c,GuruxDLMSServerExample2/dlms/include/*.h -Pattern "compress|compression|V.44|v44"
```

## Section 10 Mapping: Communication Profiles

| Profile from note | Source mapping | Functions / files |
|---|---|---|
| 3-layer HDLC-based profile | `src/dlms.c`, `src/server.c`, `src/client.c` | `dlms_useHdlc` line 70, `dlms_getHdlcFrame` line 2517, `dlms_getHdlcData` line 2904, `svr_handleSnrmRequest` line 671, `cl_snrmRequest` line 58 |
| TCP/UDP/IP COSEM_on_IP / Wrapper | `src/dlms.c` | `dlms_checkWrapperAddress` line 3197, `dlms_getTcpData` line 3301, `dlms_getWrapperFrame` line 3890 |
| CoAP-based profile | Not obvious in this checkout | No clear `coap` source file or function under `dlms/src`. |
| S-FSK PLC | `src/dlms.c`, `src/gxget.c`, `src/gxserializer.c` | `dlms_getPlcFrame` line 2671, `dlms_getPlcData` line 3464, `dlms_isPlcSfskData` line 3723, `cosem_getSFSK...` functions in `gxget.c` |
| M-Bus | `src/dlms.c`, `src/gxget.c` | `dlms_getMBusData` line 3368, `cosem_getMbusDiagnostic` line 3773, `cosem_getMbusPortSetup` line 3843 |
| LPWAN / LoRaWAN / SCHC | Not obvious in this checkout | No clear `lorawan` or `schc` module under `dlms/src`. |
| Wi-SUN | Not obvious as a named module | There are G3-PLC, PRIME, LTE, Zigbee, IPv6 objects, but no obvious `wisun` function names. |
| Gateway protocol | `src/dlms.c`, command/address handling | Search `gateway` in `dlms.c`, `server.c`, `include/enums.h`; frame prefix behavior is likely handled near PDU/frame parsing. |

## Function Index By Main Module

### `src/server.c`

```text
82    svr_handleReadRequest
89    svr_handleWriteRequest
114   sr_initialize
141   svr_initialize
238   svr_updateShortNames
315   svr_reset
327   svr_generateExceptionResponse
375   svr_HandleAarqRequest
671   svr_handleSnrmRequest
743   svr_generateDisconnectRequest
783   dlms_addFrame
919   svr_handleSetRequest2
1120  svr_getTarget
1185  svr_handleSetRequestWithList
1314  svr_hanleSetRequestWithDataBlock
1432  svr_generateConfirmedServiceError
1454  svr_handleSetRequest
1523  svr_getRequestNormal
1738  svr_getRequestNextDataBlock
1834  svr_getRequestWithList
2054  svr_handleGetRequest
2126  svr_findSNObject
2173  svr_handleRead
2243  svr_getReadData
2321  svr_handleReadBlockNumberAccess
2418  svr_handleReadDataBlockAccess
2536  svr_handleReadRequest
2628  svr_handleWriteRequest
2880  svr_handleMethodRequest
3138  svr_handleReleaseRequest
3415  svr_handleCommand
3727  svr_handleRequest
3739  svr_handleRequest3
3747  svr_handleRequest2
3819  svr_handleRequest4
4310  svr_isPushCommunicationWindowActive
4355  svr_invoke
4458  svr_handleProfileGeneric
4891  svr_run
5088  svr_monitor
5197  svr_monitorAll
5252  svr_limiter
5415  svr_limiterAll
```

### `src/client.c`

```text
58    cl_snrmRequest
178   cl_parseUAResponse
282   cl_aarqRequest
380   cl_parseAAREResponse
411   cl_getApplicationAssociationRequest
524   cl_parseApplicationAssociationResponse
613   cl_getObjectsRequest
633   cl_parseObjects
784   cl_readSN
821   cl_readLN
884   cl_readList
997   cl_read
1045  cl_readRowsByEntry
1091  cl_readRowsByRange2
1301  cl_getData
1341  cl_updateValues
1412  cl_receiverReady
1422  cl_releaseRequest
1497  cl_disconnectRequest
1603  cl_write
1644  cl_writeList
1850  cl_writeLN
1929  cl_writeSN
1969  cl_method
2016  cl_methodLN
2166  cl_methodSN
2293  cl_getServerAddress
```

### `src/dlms.c`

```text
70    dlms_useHdlc
84    dlms_checkInit
128   dlms_getGloMessage
295   dlms_getInvokeIDPriority
337   dlms_getMaxPduSize
379   dlms_setData
1991  dlms_getData
2257  dlms_checkLLCBytes
2279  dlms_getHDLCAddress
2365  dlms_checkHdlcAddress
2517  dlms_getHdlcFrame
2671  dlms_getPlcFrame
2904  dlms_getHdlcData
3197  dlms_checkWrapperAddress
3301  dlms_getTcpData
3368  dlms_getMBusData
3464  dlms_getPlcData
3602  dlms_getPlcHdlcData
3773  dlms_receiverReady
3890  dlms_getWrapperFrame
3957  dlms_handleGetResponse
4125  dlms_handleWriteResponse
4298  dlms_handleReadResponse
4421  dlms_handleMethodResponse
4525  dlms_handlePush
4734  dlms_handleDataNotification
4808  dlms_handleGbt
4897  dlms_handleGloDedRequest
5033  dlms_handleGloDedResponse
5118  dlms_handleGeneralCiphering
5216  dlms_getPdu
5503  dlms_addLLCBytes
5618  dlms_getSNPdu
5823  dlms_getLNPdu
6501  dlms_generateChallenge
6632  dlms_secure
6748  dlms_parseSnrmUaResponse
6877  dlms_isPduFull
```

### `src/gxget.c`, `src/gxset.c`, `src/gxinvoke.c`

```text
gxget.c
  861   cosem_getAssociationLogicalName
  1111  cosem_getAssociationShortName
  1504  cosem_getSecuritySetup
  1649  cosem_getIecHdlcSetup
  2080  cosem_getImageTransfer
  2592  cosem_getProfileGeneric
  2683  cosem_getDisconnectControl
  3735  cosem_getTcpUdpSetup
  4754  cosem_getPushSetup
  5505  cosem_getCompactData
  5550  cosem_getValue

gxset.c
  46    cosem_setValue

gxinvoke.c
  207   invoke_AssociationLogicalName
  474   invoke_ImageTransfer
  785   invoke_SecuritySetup
  1468  invoke_AssociationShortName
  1551  invoke_ScriptTable
  1878  invoke_Clock
  1978  invoke_Register
  2078  invoke_ProfileGeneric
  2307  invoke_DisconnectControl
  2893  invoke_ActivityCalendar
  3917  invoke_NtpSetup
  4126  cosem_invoke
```

### `src/cosem.c` And `src/gxobjects.c`

```text
cosem.c
  54    cosem_getObjectSize
  463   cosem_createObject
  517   cosem_setLogicalName
  526   cosem_init
  787   cosem_checkStructure
  823   cosem_checkArray
  1271  cosem_getVariant
  1362  cosem_setDateTimeAsOctetString
  1435  cosem_setOctetString
  1678  cosem_setVariant
  1742  getSelectedColumns
  1805  cosem_getColumns
  2017  cosem_findObjectByLN

gxobjects.c
  49    obj_getLogicalName
  767   obj_clear
  1391  obj_attributeCount
  1755  obj_getAttributeIndexToRead
  1869  obj_methodCount
  2251  clock_updateDST
  2265  clock_utcToMeterTime
```

## How To Navigate For Common Questions

| Question | Start here | Then inspect |
|---|---|---|
| How does a client open an association? | `client.c:cl_aarqRequest` | `apdu.c:apdu_generateAarq`, `server.c:svr_HandleAarqRequest`, `apdu.c:apdu_generateAARE` |
| How does the server parse a request byte stream? | `server.c:svr_handleRequest4` | `server.c:svr_handleCommand`, `dlms.c:dlms_getData2/3`, frame parser for selected interface |
| Where is GET handled? | `server.c:svr_handleGetRequest` | `gxget.c:cosem_getValue`, app callbacks in `src/main.c` |
| Where is SET handled? | `server.c:svr_handleSetRequest` | `gxset.c:cosem_setValue`, app callbacks in `src/main.c` |
| Where is ACTION handled? | `server.c:svr_handleMethodRequest` | `server.c:svr_invoke`, `gxinvoke.c:cosem_invoke` |
| Where is HDLC implemented? | `dlms.c:dlms_getHdlcData` | `dlms.c:dlms_getHdlcFrame`, `server.c:svr_handleSnrmRequest` |
| Where is WRAPPER/TCP implemented? | `dlms.c:dlms_getTcpData` | `dlms.c:dlms_getWrapperFrame`, `dlms.c:dlms_checkWrapperAddress` |
| Where is push generated? | `notify.c` | `dlms.c:dlms_handlePush`, app push code in `src/main.c` |
| Where is ciphering done? | `ciphering.c:cip_encrypt/decrypt` | `dlms.c:dlms_handleGloDedRequest/Response`, `apdu.c` authentication negotiation |

