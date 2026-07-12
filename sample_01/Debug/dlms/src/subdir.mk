################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../dlms/src/apdu.c \
../dlms/src/asn1Parser.c \
../dlms/src/bigInteger.c \
../dlms/src/bitarray.c \
../dlms/src/bytebuffer.c \
../dlms/src/ciphering.c \
../dlms/src/client.c \
../dlms/src/converters.c \
../dlms/src/cosem.c \
../dlms/src/curve.c \
../dlms/src/datainfo.c \
../dlms/src/date.c \
../dlms/src/dlms.c \
../dlms/src/dlmsSettings.c \
../dlms/src/eccPoint.c \
../dlms/src/gx509Certificate.c \
../dlms/src/gxPkcs10.c \
../dlms/src/gxaes.c \
../dlms/src/gxarray.c \
../dlms/src/gxecdsa.c \
../dlms/src/gxget.c \
../dlms/src/gxinvoke.c \
../dlms/src/gxkey.c \
../dlms/src/gxmd5.c \
../dlms/src/gxobjects.c \
../dlms/src/gxserializer.c \
../dlms/src/gxset.c \
../dlms/src/gxsetignoremalloc.c \
../dlms/src/gxsetmalloc.c \
../dlms/src/gxsha1.c \
../dlms/src/gxsha256.c \
../dlms/src/gxsha384.c \
../dlms/src/gxvalueeventargs.c \
../dlms/src/helpers.c \
../dlms/src/message.c \
../dlms/src/notify.c \
../dlms/src/objectarray.c \
../dlms/src/parameters.c \
../dlms/src/privateKey.c \
../dlms/src/publicKey.c \
../dlms/src/replydata.c \
../dlms/src/server.c \
../dlms/src/serverevents.c \
../dlms/src/shamirs.c \
../dlms/src/variant.c 

OBJS += \
./dlms/src/apdu.o \
./dlms/src/asn1Parser.o \
./dlms/src/bigInteger.o \
./dlms/src/bitarray.o \
./dlms/src/bytebuffer.o \
./dlms/src/ciphering.o \
./dlms/src/client.o \
./dlms/src/converters.o \
./dlms/src/cosem.o \
./dlms/src/curve.o \
./dlms/src/datainfo.o \
./dlms/src/date.o \
./dlms/src/dlms.o \
./dlms/src/dlmsSettings.o \
./dlms/src/eccPoint.o \
./dlms/src/gx509Certificate.o \
./dlms/src/gxPkcs10.o \
./dlms/src/gxaes.o \
./dlms/src/gxarray.o \
./dlms/src/gxecdsa.o \
./dlms/src/gxget.o \
./dlms/src/gxinvoke.o \
./dlms/src/gxkey.o \
./dlms/src/gxmd5.o \
./dlms/src/gxobjects.o \
./dlms/src/gxserializer.o \
./dlms/src/gxset.o \
./dlms/src/gxsetignoremalloc.o \
./dlms/src/gxsetmalloc.o \
./dlms/src/gxsha1.o \
./dlms/src/gxsha256.o \
./dlms/src/gxsha384.o \
./dlms/src/gxvalueeventargs.o \
./dlms/src/helpers.o \
./dlms/src/message.o \
./dlms/src/notify.o \
./dlms/src/objectarray.o \
./dlms/src/parameters.o \
./dlms/src/privateKey.o \
./dlms/src/publicKey.o \
./dlms/src/replydata.o \
./dlms/src/server.o \
./dlms/src/serverevents.o \
./dlms/src/shamirs.o \
./dlms/src/variant.o 

C_DEPS += \
./dlms/src/apdu.d \
./dlms/src/asn1Parser.d \
./dlms/src/bigInteger.d \
./dlms/src/bitarray.d \
./dlms/src/bytebuffer.d \
./dlms/src/ciphering.d \
./dlms/src/client.d \
./dlms/src/converters.d \
./dlms/src/cosem.d \
./dlms/src/curve.d \
./dlms/src/datainfo.d \
./dlms/src/date.d \
./dlms/src/dlms.d \
./dlms/src/dlmsSettings.d \
./dlms/src/eccPoint.d \
./dlms/src/gx509Certificate.d \
./dlms/src/gxPkcs10.d \
./dlms/src/gxaes.d \
./dlms/src/gxarray.d \
./dlms/src/gxecdsa.d \
./dlms/src/gxget.d \
./dlms/src/gxinvoke.d \
./dlms/src/gxkey.d \
./dlms/src/gxmd5.d \
./dlms/src/gxobjects.d \
./dlms/src/gxserializer.d \
./dlms/src/gxset.d \
./dlms/src/gxsetignoremalloc.d \
./dlms/src/gxsetmalloc.d \
./dlms/src/gxsha1.d \
./dlms/src/gxsha256.d \
./dlms/src/gxsha384.d \
./dlms/src/gxvalueeventargs.d \
./dlms/src/helpers.d \
./dlms/src/message.d \
./dlms/src/notify.d \
./dlms/src/objectarray.d \
./dlms/src/parameters.d \
./dlms/src/privateKey.d \
./dlms/src/publicKey.d \
./dlms/src/replydata.d \
./dlms/src/server.d \
./dlms/src/serverevents.d \
./dlms/src/shamirs.d \
./dlms/src/variant.d 


# Each subdirectory must supply rules for building sources it contributes
dlms/src/%.o dlms/src/%.su dlms/src/%.cyclo: ../dlms/src/%.c dlms/src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I"D:/workspace/STM32/sample_01/dlms/include" -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-dlms-2f-src

clean-dlms-2f-src:
	-$(RM) ./dlms/src/apdu.cyclo ./dlms/src/apdu.d ./dlms/src/apdu.o ./dlms/src/apdu.su ./dlms/src/asn1Parser.cyclo ./dlms/src/asn1Parser.d ./dlms/src/asn1Parser.o ./dlms/src/asn1Parser.su ./dlms/src/bigInteger.cyclo ./dlms/src/bigInteger.d ./dlms/src/bigInteger.o ./dlms/src/bigInteger.su ./dlms/src/bitarray.cyclo ./dlms/src/bitarray.d ./dlms/src/bitarray.o ./dlms/src/bitarray.su ./dlms/src/bytebuffer.cyclo ./dlms/src/bytebuffer.d ./dlms/src/bytebuffer.o ./dlms/src/bytebuffer.su ./dlms/src/ciphering.cyclo ./dlms/src/ciphering.d ./dlms/src/ciphering.o ./dlms/src/ciphering.su ./dlms/src/client.cyclo ./dlms/src/client.d ./dlms/src/client.o ./dlms/src/client.su ./dlms/src/converters.cyclo ./dlms/src/converters.d ./dlms/src/converters.o ./dlms/src/converters.su ./dlms/src/cosem.cyclo ./dlms/src/cosem.d ./dlms/src/cosem.o ./dlms/src/cosem.su ./dlms/src/curve.cyclo ./dlms/src/curve.d ./dlms/src/curve.o ./dlms/src/curve.su ./dlms/src/datainfo.cyclo ./dlms/src/datainfo.d ./dlms/src/datainfo.o ./dlms/src/datainfo.su ./dlms/src/date.cyclo ./dlms/src/date.d ./dlms/src/date.o ./dlms/src/date.su ./dlms/src/dlms.cyclo ./dlms/src/dlms.d ./dlms/src/dlms.o ./dlms/src/dlms.su ./dlms/src/dlmsSettings.cyclo ./dlms/src/dlmsSettings.d ./dlms/src/dlmsSettings.o ./dlms/src/dlmsSettings.su ./dlms/src/eccPoint.cyclo ./dlms/src/eccPoint.d ./dlms/src/eccPoint.o ./dlms/src/eccPoint.su ./dlms/src/gx509Certificate.cyclo ./dlms/src/gx509Certificate.d ./dlms/src/gx509Certificate.o ./dlms/src/gx509Certificate.su ./dlms/src/gxPkcs10.cyclo ./dlms/src/gxPkcs10.d ./dlms/src/gxPkcs10.o ./dlms/src/gxPkcs10.su ./dlms/src/gxaes.cyclo ./dlms/src/gxaes.d ./dlms/src/gxaes.o ./dlms/src/gxaes.su ./dlms/src/gxarray.cyclo ./dlms/src/gxarray.d ./dlms/src/gxarray.o ./dlms/src/gxarray.su ./dlms/src/gxecdsa.cyclo ./dlms/src/gxecdsa.d ./dlms/src/gxecdsa.o ./dlms/src/gxecdsa.su ./dlms/src/gxget.cyclo ./dlms/src/gxget.d ./dlms/src/gxget.o ./dlms/src/gxget.su ./dlms/src/gxinvoke.cyclo ./dlms/src/gxinvoke.d ./dlms/src/gxinvoke.o ./dlms/src/gxinvoke.su ./dlms/src/gxkey.cyclo ./dlms/src/gxkey.d ./dlms/src/gxkey.o ./dlms/src/gxkey.su ./dlms/src/gxmd5.cyclo ./dlms/src/gxmd5.d ./dlms/src/gxmd5.o ./dlms/src/gxmd5.su ./dlms/src/gxobjects.cyclo ./dlms/src/gxobjects.d ./dlms/src/gxobjects.o ./dlms/src/gxobjects.su ./dlms/src/gxserializer.cyclo ./dlms/src/gxserializer.d ./dlms/src/gxserializer.o ./dlms/src/gxserializer.su ./dlms/src/gxset.cyclo ./dlms/src/gxset.d ./dlms/src/gxset.o ./dlms/src/gxset.su ./dlms/src/gxsetignoremalloc.cyclo ./dlms/src/gxsetignoremalloc.d ./dlms/src/gxsetignoremalloc.o ./dlms/src/gxsetignoremalloc.su ./dlms/src/gxsetmalloc.cyclo ./dlms/src/gxsetmalloc.d ./dlms/src/gxsetmalloc.o ./dlms/src/gxsetmalloc.su ./dlms/src/gxsha1.cyclo ./dlms/src/gxsha1.d ./dlms/src/gxsha1.o ./dlms/src/gxsha1.su ./dlms/src/gxsha256.cyclo ./dlms/src/gxsha256.d ./dlms/src/gxsha256.o ./dlms/src/gxsha256.su ./dlms/src/gxsha384.cyclo ./dlms/src/gxsha384.d ./dlms/src/gxsha384.o ./dlms/src/gxsha384.su ./dlms/src/gxvalueeventargs.cyclo ./dlms/src/gxvalueeventargs.d ./dlms/src/gxvalueeventargs.o ./dlms/src/gxvalueeventargs.su ./dlms/src/helpers.cyclo ./dlms/src/helpers.d ./dlms/src/helpers.o ./dlms/src/helpers.su ./dlms/src/message.cyclo ./dlms/src/message.d ./dlms/src/message.o ./dlms/src/message.su ./dlms/src/notify.cyclo ./dlms/src/notify.d ./dlms/src/notify.o ./dlms/src/notify.su ./dlms/src/objectarray.cyclo ./dlms/src/objectarray.d ./dlms/src/objectarray.o ./dlms/src/objectarray.su ./dlms/src/parameters.cyclo ./dlms/src/parameters.d ./dlms/src/parameters.o ./dlms/src/parameters.su ./dlms/src/privateKey.cyclo ./dlms/src/privateKey.d ./dlms/src/privateKey.o ./dlms/src/privateKey.su ./dlms/src/publicKey.cyclo ./dlms/src/publicKey.d ./dlms/src/publicKey.o ./dlms/src/publicKey.su ./dlms/src/replydata.cyclo ./dlms/src/replydata.d ./dlms/src/replydata.o ./dlms/src/replydata.su ./dlms/src/server.cyclo ./dlms/src/server.d ./dlms/src/server.o ./dlms/src/server.su ./dlms/src/serverevents.cyclo ./dlms/src/serverevents.d ./dlms/src/serverevents.o ./dlms/src/serverevents.su ./dlms/src/shamirs.cyclo ./dlms/src/shamirs.d ./dlms/src/shamirs.o ./dlms/src/shamirs.su ./dlms/src/variant.cyclo ./dlms/src/variant.d ./dlms/src/variant.o ./dlms/src/variant.su

.PHONY: clean-dlms-2f-src

