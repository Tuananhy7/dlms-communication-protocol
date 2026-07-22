#include "main.h"
#include "dlms_app.h"

//TODO:
/*Data is serialized for the memory because all the boards doesn't have
EEPROM or Flash where data can be saved.*/
static unsigned char SERIALIZE_BUFFER[30000] = { 0 };

static gxSerializerSettings serializerSettings;

//Is trace used. Trace is send for UART 1. This can be used for testing purposes.
static GX_TRACE_LEVEL trace = GX_TRACE_LEVEL_VERBOSE;

//Set master key (KEK) to 1111111111111111.
static unsigned char KEK[16] = { 0x31,0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31, 0x31 };

//Space for client password.
static unsigned char PASSWORD[20];
//Space for client challenge.
static unsigned char C2S_CHALLENGE[64];
//Space for server challenge.
static unsigned char S2C_CHALLENGE[64];
//Allocate space for read list.
static gxValueEventArg events[10];

static uint32_t executeTime = 0;

static uint8_t Rx_data = 0;
static uint8_t received = 0;
extern UART_HandleTypeDef huart1;

long time_current(void)
{
	//TODO: Get current time somewhere.
	//This is not added because RTC is not installed.
	return (long)0;//time(NULL);
}

uint32_t time_elapsed(void)
{
	//TODO: Get current time somewhere.
	//This is not added because RTC is not installed.
	return (uint32_t)0;//millis();
}

void time_now(
gxtime* value)
{
	//TODO: Get current time somewhere.
	//This is not added because RTC is not installed.
	time_initUnix(value, 0);
	/*
	time_t tm1 = time(NULL);
	struct tm dt = *localtime(&tm1);
	time_init2(value, &dt);
	*/
}

uint32_t SERIALIZER_SIZE()
{
	//TODO: handle serialization. Serialization depends from the board that is not implemented.
	return sizeof(SERIALIZE_BUFFER);
}

//Read byte
extern int SERIALIZER_LOAD(uint32_t index, uint32_t count, void* value)
{
	//TODO: handle serialization. Serialization depends from the board that is not implemented.
	uint16_t pos;
	if (value == NULL)
	{
			return DLMS_ERROR_CODE_SERIALIZATION_LOAD_FAILURE;
	}
	unsigned char* p = (unsigned char*)value;
	for (pos = 0; pos != count; ++pos)
	{
			*p = SERIALIZE_BUFFER[index + pos];
			++p;
	}
	return 0;
}

//Write byte
extern int SERIALIZER_SAVE(uint32_t index, uint32_t count, const void* value)
{
	//TODO: handle serialization. Serialization depends from the board that is not implemented.
	uint16_t pos;
	if (value == NULL)
	{
			return DLMS_ERROR_CODE_SERIALIZATION_SAVE_FAILURE;
	}
	if (!((index + count) < sizeof(SERIALIZE_BUFFER)))
	{
			return DLMS_ERROR_CODE_OUTOFMEMORY;
	}
	unsigned char* p = (unsigned char*)value;
	for (pos = 0; pos != count; ++pos)
	{
			SERIALIZE_BUFFER[index + pos] = *p;
			++p;
	}
	return 0;
}

/* Private user code ---------------------------------------------------------*/

/**
 * \brief Function for putting a char in the UART buffer
 *
 * \param data the data to add to the UART buffer and send.
 *
 */
static inline int uart_write(gxByteBuffer* data)
{
	HAL_UART_Transmit(&huart1, data->data, data->size, 500);
  return 0;
}

/**
 * \brief Function for putting a trace char in the UART buffer
 *
 * \param data the data to add to the UART buffer and send.
 *
 */
static inline int uart_traceWrite(const char* data)
{
	// HAL_UART_Transmit(&huart1, (uint8_t*) data, strlen(data), 500);
  return 0;
}

///////////////////////////////////////////////////////////////////////
// Write trace to the serial port.
//
// This can be used for debugging.
///////////////////////////////////////////////////////////////////////
void GXTRACE(const char* str, const char* data)
{
  if (trace == GX_TRACE_LEVEL_VERBOSE)
  {
//		char data[10];
//    uint32_t value = HAL_GetTick();
//    uart_traceWrite((const char*) "\t:");
//		sprintf(data, " %ld", value);
//		uart_traceWrite(data);
//    uart_traceWrite((const char*) "\t");
//    uart_traceWrite(str);
//    uart_traceWrite(data);
//    uart_traceWrite((const char*) "\0");
//		HAL_Delay(10);
  }
}

///////////////////////////////////////////////////////////////////////
// Write trace to the serial port.
//
// This can be used for debugging.
///////////////////////////////////////////////////////////////////////
void GXTRACE_INT(const char* str, int32_t value)
{
  char data[10] = {0};
  //sprintf(data, " %ld", value);
  GXTRACE(str, data);
}

//DLMS settings.
dlmsServerSettings settings;
//Meter serial number.
unsigned long SERIAL_NUMBER = 123456;
//Flag ID of the meter.
const static char* FLAG_ID = "GRX";

#define HDLC_HEADER_SIZE 17
#define HDLC_BUFFER_SIZE 128
#define PDU_BUFFER_SIZE 512
#define WRAPPER_BUFFER_SIZE 8 + PDU_BUFFER_SIZE
static gxByteBuffer reply;
//Buffer where received data is saved.
static unsigned char dataBuff[64];
static gxByteBuffer data2;

//Buffer where frames are saved.
static unsigned char frameBuff[HDLC_BUFFER_SIZE + HDLC_HEADER_SIZE];
//Buffer where PDUs are saved. Add 3 bytes for LLC bytes.
static unsigned char pduBuff[3 + PDU_BUFFER_SIZE];
static unsigned char replyFrame[PDU_BUFFER_SIZE + HDLC_HEADER_SIZE];
//Define server system title.
static unsigned char SERVER_SYSTEM_TITLE[8] = { 0 };

static gxData ldn;
static gxIecHdlcSetup hdlc;
//Don't use clock as a name. Some compilers are using clock as reserved word.
static gxClock clock1;
gxAssociationLogicalName association;
static gxRegister activePowerL1;

static gxObject* ALL_OBJECTS[] = { BASE(association), BASE(ldn), BASE(clock1), BASE(activePowerL1), BASE(hdlc) };

/////////////////////////////////////////////////////////////////////////////
// Save data to the EEPROM.
//
// Only updated value is saved. This is done because write to EEPROM is slow
// and there is a limit how many times value can be written to the EEPROM.
/////////////////////////////////////////////////////////////////////////////
int saveSettings(gxObject* savedObject, uint16_t savedAttributes)
{
  int ret = 0;
  serializerSettings.savedObject = savedObject;
  serializerSettings.savedAttributes = savedAttributes;
  if ((ret = ser_saveObjects(&serializerSettings, ALL_OBJECTS, sizeof(ALL_OBJECTS) / sizeof(ALL_OBJECTS[0]))) != 0)
  {
    GXTRACE_INT(GET_STR_FROM_EEPROM("saveObjects failed: "), ret);
  }
  else
  {
    GXTRACE_INT(GET_STR_FROM_EEPROM("saveObjects succeeded. Index: "), serializerSettings.updateStart);
    GXTRACE_INT(GET_STR_FROM_EEPROM("Count: "), serializerSettings.updateEnd - serializerSettings.updateStart);
  }
  return ret;
}


/////////////////////////////////////////////////////////////////////////////
// Load data from the EEPROM.
// Returns serialization version or zero if data is not saved.
/////////////////////////////////////////////////////////////////////////////
int loadSettings()
{
  int ret = 0;
  serializerSettings.position = 0;
 //MIKKO ret = ser_loadObjects(&settings.base, &serializerSettings, ALL_OBJECTS, sizeof(ALL_OBJECTS) / sizeof(ALL_OBJECTS[0]));
  if (ret != 0)
  {
    GXTRACE_INT(GET_STR_FROM_EEPROM("Failed to load settings from EEPROM."), serializerSettings.position);
  }
  return ret;
}

///////////////////////////////////////////////////////////////////////
//This method adds example Logical Name Association object.
///////////////////////////////////////////////////////////////////////
int addAssociation()
{
	const unsigned char ln[6] = { 0, 0, 40, 0, 1, 255 };
	cosem_init2(BASE(association), DLMS_OBJECT_TYPE_ASSOCIATION_LOGICAL_NAME, ln);
	//Only Logical Device Name is add to this Association View.
	//Use this if you  need to save heap.
	oa_attach(&association.objectList, ALL_OBJECTS, sizeof(ALL_OBJECTS) / sizeof(ALL_OBJECTS[0]));
	bb_addString(&association.secret, "Gurux");
	association.authenticationMechanismName.mechanismId = DLMS_AUTHENTICATION_NONE;
	return 0;
}

///////////////////////////////////////////////////////////////////////
//Add Logical Device Name. 123456 is meter serial number.
///////////////////////////////////////////////////////////////////////
// COSEM Logical Device Name is defined as an octet-string of 16 octets.
// The first three octets uniquely identify the manufacturer of the device and it corresponds
// to the manufacturer's identification in IEC 62056-21.
// The following 13 octets are assigned by the manufacturer.
//The manufacturer is responsible for guaranteeing the uniqueness of these octets.
int addLogicalDeviceName() {
	int ret;
	const unsigned char ln[6] = { 0, 0, 42, 0, 0, 255 };
	if ((ret = INIT_OBJECT(ldn, DLMS_OBJECT_TYPE_DATA, ln)) == 0)
	{
			//Define Logical Device Name.
			static char LDN[17];
			sprintf(LDN, "%s%.13lu", FLAG_ID, SERIAL_NUMBER);
			GX_OCTET_STRING(ldn.value, LDN, sizeof(LDN));
	}
	return ret;
}

///////////////////////////////////////////////////////////////////////
//This method adds example clock object.
///////////////////////////////////////////////////////////////////////
int addClockObject()
{
	int ret = 0;
	//Add default clock. Clock's Logical Name is 0.0.1.0.0.255.
	const unsigned char ln[6] = { 0, 0, 1, 0, 0, 255 };
	if ((ret = INIT_OBJECT(clock1, DLMS_OBJECT_TYPE_CLOCK, ln)) == 0)
	{
		//Set default values.
		time_init(&clock1.begin, -1, 3, -1, 2, 0, 0, 0, 0);
		clock1.begin.extraInfo = DLMS_DATE_TIME_EXTRA_INFO_LAST_DAY;
		time_init(&clock1.end, -1, 10, -1, 3, 0, 0, 0, 0);
		clock1.end.extraInfo = DLMS_DATE_TIME_EXTRA_INFO_LAST_DAY;
		//Meter is using UTC time zone.
		clock1.timeZone = 0;
		//Deviation is 60 minutes.
		clock1.deviation = 60;
		clock1.clockBase = DLMS_CLOCK_BASE_FREQUENCY_50;
	}
	//Set default clock.
	settings.defaultClock = &clock1;
	return ret;
}


///////////////////////////////////////////////////////////////////////
//Add IEC HDLC Setup object.
///////////////////////////////////////////////////////////////////////
int addIecHdlcSetup()
{
	int ret = 0;
	unsigned char ln[6] = { 0, 0, 22, 0, 0, 255 };
	if ((ret = INIT_OBJECT(hdlc, DLMS_OBJECT_TYPE_IEC_HDLC_SETUP, ln)) == 0)
	{
		hdlc.communicationSpeed = DLMS_BAUD_RATE_9600;
		hdlc.windowSizeReceive = hdlc.windowSizeTransmit = 1;
		hdlc.maximumInfoLengthTransmit = hdlc.maximumInfoLengthReceive = 128;
		hdlc.inactivityTimeout = 120;
		hdlc.deviceAddress = 0x10;
	}
	settings.hdlc = &hdlc;
	return ret;
}

///////////////////////////////////////////////////////////////////////
//This method adds example register object.
///////////////////////////////////////////////////////////////////////
int addRegisterObject()
{
	const unsigned char ln[6] = { 1,1,21,25,0,255 };
	cosem_init2((gxObject*)&activePowerL1, DLMS_OBJECT_TYPE_REGISTER, ln);
	//10 ^ 3 =  1000
	activePowerL1.scaler = 3;
	activePowerL1.unit = 30;
	return 0;
}

int svr_findObject(
dlmsSettings* settings,
DLMS_OBJECT_TYPE objectType,
int sn,
unsigned char* ln,
gxValueEventArg *e)
{
	if (objectType == DLMS_OBJECT_TYPE_ASSOCIATION_LOGICAL_NAME)
	{
		e->target = &association.base;
	}
	return 0;
}

/////////////////////////////////////////////////////////////////////////////
//
/////////////////////////////////////////////////////////////////////////////
void svr_preRead(
dlmsSettings* settings,
gxValueEventCollection* args)
{
	gxValueEventArg *e;
	int ret, pos;
	DLMS_OBJECT_TYPE type;
	for (pos = 0; pos != args->size; ++pos)
	{
		if ((ret = vec_getByIndex(args, pos, &e)) != 0)
		{
			return;
		}
		//Let framework handle Logical Name read.
		if (e->index == 1)
		{
			continue;
		}

		//Get target type.
		type = (DLMS_OBJECT_TYPE)e->target->objectType;
		//Let Framework will handle Association objects and profile generic automatically.
		if (type == DLMS_OBJECT_TYPE_ASSOCIATION_LOGICAL_NAME ||
		type == DLMS_OBJECT_TYPE_ASSOCIATION_SHORT_NAME)
		{
			continue;
		}
		//Update value by one every time when user reads register.
		if (e->target == &activePowerL1.base && e->index == 2)
		{
			var_setUInt16(&activePowerL1.value, activePowerL1.value.uiVal + 1);
		}
		//Get time if user want to read date and time.
		if (e->target == &clock1.base && e->index == 2)
		{
			time_now(&((gxClock*)e->target)->time);
		}
	}
}

/////////////////////////////////////////////////////////////////////////////
//
/////////////////////////////////////////////////////////////////////////////
void svr_preWrite(
dlmsSettings* settings,
gxValueEventCollection* args)
{
	#if defined(_WIN32) || defined(_WIN64) || defined(__linux__)//If Windows or Linux
	char str[25];
	gxValueEventArg *e;
	int ret, pos;
	for (pos = 0; pos != args->size; ++pos)
	{
		if ((ret = vec_getByIndex(args, pos, &e)) != 0)
		{
			return;
		}
		hlp_getLogicalNameToString(e->target->logicalName, str);
		printf("Writing %s\r\n", str);

	}
	#endif //defined(_WIN32) || defined(_WIN64) || defined(__linux__)//If Windows or Linux
}

/////////////////////////////////////////////////////////////////////////////
//
/////////////////////////////////////////////////////////////////////////////
void svr_preAction(
dlmsSettings* settings,
gxValueEventCollection* args)
{
	#if defined(_WIN32) || defined(_WIN64) || defined(__linux__)//If Windows or Linux
	char str[25];
	#endif
	gxValueEventArg *e;
	int ret, pos;
	for (pos = 0; pos != args->size; ++pos)
	{
		if ((ret = vec_getByIndex(args, pos, &e)) != 0)
		{
			return;
		}
		#if defined(_WIN32) || defined(_WIN64) || defined(__linux__)//If Windows or Linux
		hlp_getLogicalNameToString(e->target->logicalName, str);
		printf("Action %s:%d\n", str, e->index);
		#endif
	}
}

/////////////////////////////////////////////////////////////////////////////
//
/////////////////////////////////////////////////////////////////////////////
void svr_postRead(
dlmsSettings* settings,
gxValueEventCollection* args)
{
}
/////////////////////////////////////////////////////////////////////////////
//
/////////////////////////////////////////////////////////////////////////////
void svr_postWrite(
dlmsSettings* settings,
gxValueEventCollection* args)
{
}

/////////////////////////////////////////////////////////////////////////////
//
/////////////////////////////////////////////////////////////////////////////
void svr_postAction(
dlmsSettings* settings,
gxValueEventCollection* args)
{
	gxValueEventArg *e;
	int ret, pos;
	for (pos = 0; pos != args->size; ++pos)
	{
		if ((ret = vec_getByIndex(args, pos, &e)) != 0)
		{
			return;
		}
	}
}

unsigned char svr_isTarget(
	dlmsSettings* settings,
	uint32_t serverAddress,
	uint32_t clientAddress)
{
	//Check server address using serial number.
	if ((serverAddress & 0x3FFF) == SERIAL_NUMBER % 10000 + 1000)
	{
		return 1;
	}
	//Check server address with two bytes.
	if ((serverAddress & 0xFFFF0000) == 0 && (serverAddress & 0x7FFF) == 1)
	{
		return 1;
	}
	//Check server address with one byte.
	if ((serverAddress & 0xFFFFFF00) == 0 && (serverAddress & 0x7F) == 1)
	{
		return 1;
	}
	return 0;
}

DLMS_SOURCE_DIAGNOSTIC svr_validateAuthentication(
dlmsServerSettings* settings,
DLMS_AUTHENTICATION authentication,
gxByteBuffer* password)
{
	if (authentication == DLMS_AUTHENTICATION_NONE)
	{
		//Uncomment this if authentication is always required.
		//return DLMS_SOURCE_DIAGNOSTIC_AUTHENTICATION_MECHANISM_NAME_REQUIRED;
		return DLMS_SOURCE_DIAGNOSTIC_NONE;
	}
	//Uncomment this if only authentication None is supported.
	//return DLMS_SOURCE_DIAGNOSTIC_NO_REASON_GIVEN;
	return DLMS_SOURCE_DIAGNOSTIC_NONE;
}

/**
* Get attribute access level.
*/
DLMS_ACCESS_MODE svr_getAttributeAccess(
dlmsSettings *settings,
gxObject *obj,
unsigned char index)
{
	if (index == 1)
	{
		return DLMS_ACCESS_MODE_READ;
	}
	// Only read is allowed
	if (settings->authentication == DLMS_AUTHENTICATION_NONE)
	{
		return DLMS_ACCESS_MODE_READ;
	}
	// Only clock write is allowed.
	if (settings->authentication == DLMS_AUTHENTICATION_LOW)
	{
		if (obj->objectType == DLMS_OBJECT_TYPE_CLOCK)
		{
			return DLMS_ACCESS_MODE_READ_WRITE;
		}
		return DLMS_ACCESS_MODE_READ;
	}
	// All writes are allowed.
	return DLMS_ACCESS_MODE_READ_WRITE;
}

/**
* Get method access level.
*/
DLMS_METHOD_ACCESS_MODE svr_getMethodAccess(
dlmsSettings *settings,
gxObject *obj,
unsigned char index)
{
	// Methods are not allowed.
	if (settings->authentication == DLMS_AUTHENTICATION_NONE)
	{
		return DLMS_METHOD_ACCESS_MODE_NONE;
	}
	// Only clock methods are allowed.
	if (settings->authentication == DLMS_AUTHENTICATION_LOW)
	{
		if (obj->objectType == DLMS_OBJECT_TYPE_CLOCK)
		{
			return DLMS_METHOD_ACCESS_MODE_ACCESS;
		}
		return DLMS_METHOD_ACCESS_MODE_NONE;
	}
	return DLMS_METHOD_ACCESS_MODE_ACCESS;
}

/////////////////////////////////////////////////////////////////////////////
//Client has made connection to the server.
/////////////////////////////////////////////////////////////////////////////
int svr_connected(
dlmsServerSettings *settings)
{
	return 0;
}

/**
* Client has try to made invalid connection. Password is incorrect.
*
* @param connectionInfo
*            Connection information.
*/
int svr_invalidConnection(dlmsServerSettings *settings)
{
	return 0;
}

/////////////////////////////////////////////////////////////////////////////
// Client has close the connection.
/////////////////////////////////////////////////////////////////////////////
int svr_disconnected(
dlmsServerSettings *settings)
{
	return 0;
}

void svr_preGet(
dlmsSettings* settings,
gxValueEventCollection* args)
{
	gxValueEventArg *e;
	int ret, pos;
	for (pos = 0; pos != args->size; ++pos)
	{
		if ((ret = vec_getByIndex(args, pos, &e)) != 0)
		{
			return;
		}
	}
}

void svr_postGet(
dlmsSettings* settings,
gxValueEventCollection* args)
{

}

int createObjects()
{
	int ret;
	OA_ATTACH(settings.base.objects, ALL_OBJECTS);
	if ((ret = addLogicalDeviceName()) != 0 ||
    (ret = addClockObject()) != 0 ||
    (ret = addRegisterObject()) != 0 ||
		(ret = addIecHdlcSetup()) != 0 ||
    (ret = addAssociation()) != 0)
	{
		executeTime = 0;
	}
	if ((ret = loadSettings()) != 0)
  {
    GXTRACE_INT(GET_STR_FROM_EEPROM("Failed to load settings from EEPROM."), ret);
    executeTime = 0;
  }
  GXTRACE(GET_STR_FROM_EEPROM("Meter started."), NULL);   
  return ret ;
}


void Receive(UART_HandleTypeDef *huart){
	if (huart->Instance == huart1.Instance)
	{
		bb_setUInt8(&data2, Rx_data);
		HAL_UART_Receive_IT(&huart1, &Rx_data, 1);
		received = 1;
	}
}

int dlms_app_entry(void)
{

  /* USER CODE BEGIN 1 */
	int ret;
	HAL_UART_Receive_IT(&huart1, &Rx_data, 1); // rx_data là biến uint8_t toàn cục
	//Add FLAG ID.
	memcpy(SERVER_SYSTEM_TITLE, FLAG_ID, 3);
	//ADD serial number.
	memcpy(SERVER_SYSTEM_TITLE + 4, &SERIAL_NUMBER, 4);
	bb_attach(&data2, dataBuff, 0, sizeof(dataBuff));
	bb_attach(&reply, replyFrame, 0, sizeof(replyFrame));

	//Start server using logical name referencing and HDLC framing.
	svr_init(&settings, 1, DLMS_INTERFACE_TYPE_HDLC, HDLC_BUFFER_SIZE, PDU_BUFFER_SIZE, frameBuff, sizeof(frameBuff), pduBuff, sizeof(pduBuff));
    //Allocate space for read list.
    vec_attach(&settings.transaction.targets, events, 0, sizeof(events) / sizeof(events[0]));
	//Allocate space for client password.
	BB_ATTACH(settings.base.password, PASSWORD, 0);
	//Allocate space for client challenge.
	BB_ATTACH(settings.base.ctoSChallenge, C2S_CHALLENGE, 0);
	//Allocate space for server challenge.
	BB_ATTACH(settings.base.stoCChallenge, S2C_CHALLENGE, 0);
	memcpy(settings.base.kek, KEK, sizeof(KEK));
	//Add COSEM objects.
	if ((ret = createObjects()) != 0)
	{
		 return ret;
	}
	svr_initialize(&settings);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */
    /* USER CODE BEGIN 3 */
	  if (received)
	  {
		if (svr_handleRequest(&settings, &data2, &reply) != 0)
		{
			bb_clear(&reply);
		}
		bb_clear(&data2);
		received = 0;
		if (reply.size != 0)
		{
			uart_write(&reply);
		}
	}
	//HAL_Delay(1000);
  }
  /* USER CODE END 3 */
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
 if (huart->Instance == USART1)
 {
   Receive(huart);
 }
}