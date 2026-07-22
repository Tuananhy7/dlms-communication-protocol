//
// --------------------------------------------------------------------------
//  Gurux Ltd
//
//
//
// Filename:        $HeadURL:  $
//
// Version:         $Revision:  $,
//                  $Date:  $
//                  $Author: $
//
// Copyright (c) Gurux Ltd
//
//---------------------------------------------------------------------------

#ifndef CONNECTION_H
#define CONNECTION_H

#include "../../dlms/include/bytebuffer.h"
#include "../../dlms/include/dlmssettings.h"

#include <Windows.h> //Add support for serial port functions.

static const unsigned int RECEIVE_BUFFER_SIZE = 200;

#ifdef  __cplusplus
extern "C" {
#endif

typedef struct
{
    //Is trace used.
    unsigned char trace;
    //Socked handle.
    SOCKET socket;
    //Serial port handle.
    HANDLE comPort;
    OVERLAPPED		osWrite;
    OVERLAPPED		osReader;

    //Receiver thread handle.
    HANDLE receiverThread;
    unsigned long   waitTime;
    //Received data.
    gxByteBuffer data;
    //If receiver thread is closing.
    unsigned char closing;
    dlmsServerSettings settings;
} connection;

void con_initializeBuffers(
    connection* connection,
    int size);

int svr_listen(
    connection* con,
    unsigned short port);

//Close connection..
int con_close(
    connection* con);

#ifdef  __cplusplus
}
#endif

#endif //CONNECTION_H
