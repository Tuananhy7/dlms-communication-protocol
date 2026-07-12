#ifndef __DLMS_APP_H
#define __DLMS_APP_H

#ifdef __cplusplus
extern "C" {
#endif

//printf needs this,
#include <stdio.h>

#include "../../dlms/include/bytebuffer.h"
#include "../../dlms/include/dlmssettings.h"
#include "../../dlms/include/variant.h"
#include "../../dlms/include/cosem.h"
#include "../../dlms/include/server.h"
#include "../../dlms/include/date.h"
#include "../../dlms/include/gxserializer.h"

void MX_USART2_UART_Init(void);
int dlms_app_entry(void);

#ifdef __cplusplus
}
#endif
#endif /* __DLMS_APP_H */