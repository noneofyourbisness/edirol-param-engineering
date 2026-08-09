#pragma once
#pragma warning(disable : 4996)
#include <iostream>

typedef unsigned char	u8;
typedef unsigned short	u16;
typedef unsigned int	u32;

int HexArrayToInt(u8* Array)
{
	int A = 0;
	int* Final = &A;
	Final = (int*)Array;

	return *Final;
}

int SetLowByte(int Value, u8 Byte)
{
	u8* ExtraBytes = (u8*)malloc(4);

	memcpy(ExtraBytes, &Value, 4);

	ExtraBytes[0] = Byte;

	memcpy(&Value, ExtraBytes, 4);

	free(ExtraBytes);

	return Value;
}

void DecodeArray1(u8* DecodeMap, u8* Buffer, unsigned int Position, u8* ExBuffer, unsigned int Size)
{

	//memset(ExBuffer, 0, ASize);

	unsigned int var1 = 0;
	u8 MoveByte = 0;
	u8 Byte = 0;
	int Extra = 0;
	for (unsigned int i = 0; i < Size; i++)
	{
		var1 = i;
		var1 = var1 & 0xff;
		Extra = SetLowByte(i, 0);

		MoveByte = DecodeMap[var1];
		Byte = Buffer[Position + MoveByte + Extra];
		ExBuffer[i] = Byte;
	}

}

class EncryptionController
{
public:
	u8* HeaderBuffer;
	u8* Data;
	EncryptionController(u8* Data)
	{
		u8* HeaderBuffer = (u8*)malloc(428);
		memcpy(HeaderBuffer,Data,428);

		this->HeaderBuffer = HeaderBuffer;
		this->Data = Data;
	}

	int GetData1(u8* Data, int a2, int a3)
	{
		u8* Data1 = this->Data;
		Data1 -= 20;

		int result; // eax

		switch (a2)
		{
		case 0:

			result = HexArrayToInt(&Data1[304]);
			break;
		case 1:
			result = HexArrayToInt(&Data1[312]);
			break;
		case 2:
			result = HexArrayToInt(&Data1[320]);
			break;
		case 3:
			result = HexArrayToInt(&Data1[(8 * a3) + 332]);
			break;
		case 4:
			result = HexArrayToInt(&Data1[(8 * a3) + 372]);
			break;
		case 5:
			result = HexArrayToInt(&Data1[(8 * a3) + 412]);
			break;
		default:
			result = 0;
			break;
		}
		return result;
	}

	int GetData2(int a2, int a3)
	{
		u8* Data1 = this->Data;
		Data1 -= 20;

		int result; // eax

		int Add = 0x1ac;

		switch (a2)
		{
		case 0:
			result = HexArrayToInt(&Data1[300]);
			break;
		case 1:
			result = HexArrayToInt(&Data1[308]);
			break;
		case 2:
			result = HexArrayToInt(&Data1[316]);
			break;
		case 3:
			result = HexArrayToInt(&Data1[(8 * a3) + 328]);
			break;
		case 4:
			result = HexArrayToInt(&Data1[(8 * a3) + 368]);
			break;
		case 5:
			result = HexArrayToInt(&Data1[(8 * a3) + 408]);
			break;
		default:
			result = 0;
			break;
		}
		return result + Add;
	}

	u8* DecodeArray(u8* Buffer, unsigned int Position, unsigned int Size)
	{
		u8* Total = (u8*)malloc(Size);

		//for (int i = 0; i < Count; i++)
		{
			u8* BufferClone = (u8*)malloc(Size);
			u8* ExBuffer = (u8*)malloc(Size);

			//int Minari = Size - Position;

			memcpy(BufferClone, &Buffer[Position], Size);
			DecodeArray1(Buffer + 24, BufferClone, 0, ExBuffer, Size);

			memcpy(Total, ExBuffer, Size);
			free(ExBuffer);
			free(BufferClone);
		}

		return Total;
	}

	u8* EncodeArray(u8* Buffer, unsigned int Size)
	{
		u8* Total = (u8*)malloc(Size);
		int i = 0;

		{
			u8* ExBuffer = (u8*)malloc(Size);

			unsigned int var1 = 0;
			u8 MoveByte = 0;
			u8 Byte = 0;
			int Extra = 0;
			for (unsigned int i = 0; i < Size; i++)
			{
				var1 = i;
				var1 = var1 & 0xff;
				Extra = SetLowByte(i, 0);

				MoveByte = this->HeaderBuffer[var1+24];
				Byte = Buffer[i];
				ExBuffer[MoveByte + Extra] = Byte;
			}


			memcpy(Total, ExBuffer, Size);
			free(ExBuffer);
		}

		return Total;
	}
};