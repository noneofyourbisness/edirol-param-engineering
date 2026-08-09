#include "EncryptionController.h"

int SetLowByte(int Value, u8 Byte)
{
	u8* ExtraBytes = (u8*)malloc(4);

	memcpy(ExtraBytes, &Value, 4);

	ExtraBytes[0] = Byte;

	memcpy(&Value, ExtraBytes, 4);

	free(ExtraBytes);

	return Value;
}
