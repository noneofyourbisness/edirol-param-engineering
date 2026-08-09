#pragma once
#include <iostream>
#include <vector>;

typedef uint8_t		u8;
typedef uint16_t	u16;
typedef uint32_t	u32;

int HexArrayToInt(u8*);

int ReverseInt(int Value)
{
	u8 Array[4];
	u8 Array1[4];

	memcpy(Array, &Value, 4);

	Array1[0] = Array[3];
	Array1[1] = Array[2];
	Array1[2] = Array[1];
	Array1[3] = Array[0];

	return HexArrayToInt(Array1);
}

unsigned int ReverseUInt(unsigned int Value)
{
	u8 Array[4];
	u8 Array1[4];

	memcpy(Array, &Value, 4);

	Array1[0] = Array[3];
	Array1[1] = Array[2];
	Array1[2] = Array[1];
	Array1[3] = Array[0];

	return HexArrayToInt(Array1);
}


unsigned int HexArrayToUInt(u8* Array)
{
	unsigned int A = 0;
	unsigned int* Final = &A;
	Final = (unsigned int*)Array;

	return *Final;
}

unsigned int HexArrayToUInt2(u8* Array)
{
	unsigned int Value = 0;

	memcpy(&Value, Array, 4);

	return Value;
}

unsigned int sub_10040DA0(u8* Buffer, u8* Map, int Byte, int* dword_1009E5F8)
{
	u8* BufferPointer_1; // ebp
	u8 MapByte; // cl
	u8 *BufferPointer; // edx
	int LoopIndex; // eax
	u8 LoopIndex_1; // esi
	unsigned int Number; // ebx
	unsigned int result; // eax

	BufferPointer_1 = *Map + Buffer;
	MapByte = Map[2];

	if ((MapByte & 128u) != 0)
		MapByte = -MapByte;

	BufferPointer = (*Map + Buffer);
	LoopIndex = (MapByte + Map[3]);
	LoopIndex_1 = -LoopIndex;
	Number = 0;

	int Aaaa0 = 0;
	int Aaaa1 = 0;

	for(; LoopIndex > 0;)
	{
		LoopIndex -= 8;
		LoopIndex_1 = (LoopIndex_1 + 8);
		Number = *BufferPointer++ | (Number << 8);
	};

	result = Number & ~(dword_1009E5F8[(MapByte)-1] << (LoopIndex_1)) | (dword_1009E5F8[(MapByte)-1] << (LoopIndex_1)) & (Byte << LoopIndex_1);

		do
		{
			*--BufferPointer = (u8)(result);
			result >>= 8;
		} while (BufferPointer > BufferPointer_1);
	return result;
}

unsigned int __cdecl sub_10041540(u8* a1, u8* Map, int Byte, int* dword_1009E5F8)
{
	int v4; // eax
	int v5; // ecx
	char v6; // al
	int Byte_1; // eax
	u8 Mapa; // [esp+14h] [ebp+8h]

	v4 = *(Map + 4);
	if (*(Map + 8) - v4 >= 0 || *(Map + 4) >= 0x40u)
		v5 = 0;
	else
		v5 = 64 - v4;
	v6 = *(Map + 2);
	if (v6 < 0)
		v6 = -v6;
	Mapa = v6;
	Byte_1 = Byte;
	if (Byte - v5 > dword_1009E5F8[Mapa - 1])
		Byte_1 = v5 + *(Map + 6);
	return sub_10040DA0(a1, Map, Byte_1 - v5, dword_1009E5F8);
}

int __cdecl sub_10041410(u8* a1, u8* a2, u8 *a3, int a4, int* dword_1009E5F8)
{
	int v4; // ebx
	int v5; // esi
	int v8; // edx
	int v9; // ecx
	int v11; // ecx
	unsigned __int8 v12; // dl
	unsigned int v13; // eax
	int v15; // [esp+10h] [ebp-8h]
	int v16; // [esp+14h] [ebp-4h]
	unsigned __int8 v17; // [esp+20h] [ebp+8h]
	int v18; // [esp+24h] [ebp+Ch]
	int v19; // [esp+28h] [ebp+10h]

	v4 = a4;
	v5 = 0;
	v15 = 0;
	if (a4 <= 0)
		return v15;
	while (1)
	{
		v8 = (char)*(a2 + 2);
		v19 = --v4;
		if (v8 >= 0)
		{
			v13 = (*a3);
			++a3;
			sub_10041540(a1, a2, v13, dword_1009E5F8);
		LABEL_14:
			a2 += 12;
			++v15;
			goto LABEL_15;
		}
		v18 = 0;
		v9 = -v8;
		v16 = 0;
		if (-v8 < 8)
			break;
	LABEL_8:
		v11 = -(v8 + v18);
		if (v11 < 8)
		{
			v12 = (*a3);
			++a3;
			if (v12 > dword_1009E5F8[v11 - 1])
				v5 = -1;
			sub_10041540(a1, a2, v5 | v12, dword_1009E5F8);
			v15 += v16;
			goto LABEL_14;
		}
		++a3;
		a2 += 12;
	LABEL_15:
		v5 = 0;
		if (v4 <= 0)
			return v15;
	}
	while (1)
	{
		v17 = *a3;
		v18 -= v8;
		++a3;
		if (v17 > dword_1009E5F8[(-v8) - 1 ])
			v5 = -1;
		a2 += 12;
		++v16;
		v5 = (v5 | v17) << v9;
		v4 = v19 - 1;
		if (v19-- == 0)
			return v15;
		v8 = (char)*(a2 + 2);
		v9 = -v8;
		if (-v8 >= 8)
			goto LABEL_8;
	}
}

u8 AAaaaaa[] = {0xAD,0xBA,0x0D,0xF0};

u8* sub_404E50Encode(u8 *Buffer, u8* Map, int Add, int InstCount, int* dword_451948)
{
	u8* FileBuffer; // eax
	u8* FileBufferPointer; // edi
	int Position; // ebx
	u8* FileBufferPointer_1; // edi
	unsigned __int8 *v11; // ebp
	bool v12; // zf
	size_t Size; // [esp-8h] [ebp-34h]
	int Position_1; // [esp+30h] [ebp+4h]
	int FinalBankCount; // [esp+38h] [ebp+Ch]
	int Adda; // [esp+38h] [ebp+Ch]
	int LoopIndex; // [esp+3Ch] [ebp+10h]


	FinalBankCount = InstCount + Add;
	Size = 574 * InstCount + 14;

	FileBuffer = (u8*)malloc(Size);
	memset(FileBuffer, 0, Size);

	((int*)FileBuffer)[0] = InstCount / 0xff;
	((int*)FileBuffer)[1] = 234881024;
	((int*)FileBuffer)[2] = 1040318464;
	//*Buffer = FileBuffer;
	//*FileBuffer = (InstCount << 8) ^ BYTE1(InstCount);
	//FileBuffer[1] = 234881024;
	//FileBuffer[2] = 1040318464;
	*(FileBuffer + 6) = 0;
	FileBufferPointer = FileBuffer + 14;

	for (int i = 0; i < (Size-14) / 4; i++)
	{
		memcpy(FileBufferPointer + i*4,AAaaaaa,4);
	}

	if (Add < FinalBankCount)
	{
		Position = 948 * Add;
		LoopIndex = FinalBankCount - Add;
		do
		{
			sub_10041410(FileBufferPointer, Map + 12 * 0x242, (Position + Buffer), 79, dword_451948);
			FileBufferPointer_1 = FileBufferPointer + 56;
			sub_10041410(FileBufferPointer_1, Map + 12 * 0x294, (Buffer + Position + 79), 145, dword_451948);
			FileBufferPointer_1 += 78;
			sub_10041410(FileBufferPointer_1, Map + 12 * 0x328, (Buffer + Position + 224), 52, dword_451948);
			FileBufferPointer_1 += 26;
			sub_10041410(FileBufferPointer_1, Map + 12 * 0x35D, (Buffer + Position + 276), 83, dword_451948);
			FileBufferPointer_1 += 42;
			sub_10041410(FileBufferPointer_1, Map + 12 * 0x3B1, (Buffer + Position + 359), 41, dword_451948);
			FileBufferPointer = FileBufferPointer_1 + 32;
			Position_1 = Position;
			Adda = 4;
			do
			{
				v11 = (Buffer + Position_1 + 400);
				sub_10041410(FileBufferPointer, Map + 12 * 0x3D8 + 36, v11, 137, dword_451948);
				FileBufferPointer += 85;
				v12 = Adda == 1;
				Position_1 += 137;
				--Adda;
			} while (!v12);
			Position += 948;
			--LoopIndex;
		} while (LoopIndex);
	}
	return FileBuffer;
}

u8* RhythmEncode(u8 *Buffer, u8* Map, int Offset, int InstCount, int* dword_451948)
{
	u8* FileBuffer; // eax
	u8* FileBufferPointer; // edi
	int Position; // ebx
	u8* FileBufferPointer_1; // edi
	unsigned __int8 *v11; // ebp
	unsigned int v12; // zf
	size_t Size; // [esp-8h] [ebp-34h]
	int Position_1; // [esp+30h] [ebp+4h]
	int FinalBankCount; // [esp+38h] [ebp+Ch]
	int Adda; // [esp+38h] [ebp+Ch]
	int LoopIndex; // [esp+3Ch] [ebp+10h]

	InstCount -= Offset;

	Size = 11160 * InstCount + 20;

	FileBuffer = (u8*)malloc(Size);
	//memset(FileBuffer, 0, Size);
	((int*)FileBuffer)[0] = 0;
	FileBuffer[1] = InstCount;
	((int*)FileBuffer)[1] = 335544320;
	((int*)FileBuffer)[2] = 942276608;
	FileBuffer[12] = 0;
	FileBuffer[12 + 1] = 0;
	//*Buffer = FileBuffer;
	//*FileBuffer = (InstCount << 8) ^ BYTE1(InstCount);
	//FileBuffer[1] = 234881024;
	//FileBuffer[2] = 1040318464;
	*(FileBuffer + 6) = 0;
	FileBufferPointer = FileBuffer + 20;

	/*for (int i = 0; i < (Size-14) / 4; i++)
	{
		memcpy(FileBufferPointer + i*4,AAaaaaa,4);
	}*/

	Position = 17282 * Offset;

	unsigned int v13 = 0;
	unsigned int LoopIndex_1 = 0;
	unsigned int v20 = (InstCount << 9) + 10648 * 0 + 20;
	unsigned int LoopIndex_2 = InstCount - 0;
	do
	{
		sub_10041410(FileBufferPointer, Map + 12 * 0x46c, (Position + Buffer), 18, dword_451948);
		FileBufferPointer_1 = FileBufferPointer + 14;
		sub_10041410(FileBufferPointer_1, Map + 12 * 0x480, (Buffer + Position + 18), 145, dword_451948);
		FileBufferPointer_1 += 78;
		sub_10041410(FileBufferPointer_1, Map + 12 * 0x514, (Buffer + Position + 163), 52, dword_451948);
		FileBufferPointer_1 += 26;
		sub_10041410(FileBufferPointer_1, Map + 12 * 0x549, (Buffer + Position + 215), 83, dword_451948);
		LoopIndex_1 = v20;
		FileBufferPointer = FileBufferPointer_1 + 42;
		LoopIndex = 88;
		do
		{
			v12 = (LoopIndex_1 >> 16) | LoopIndex_1 & 0xFF0000;
			FileBufferPointer += 4;
			v13 = LoopIndex_1 & 0xFF00 | (LoopIndex_1 << 16);
			LoopIndex_1 += 121;
			unsigned int Value = (v13 << 8) | (v12 >> 8);
			memcpy(FileBufferPointer - 4, &Value, 4);
			--LoopIndex;
		} while (LoopIndex);
		v20 = LoopIndex_1;
		Position += 17282;
		--LoopIndex_2;
	} while (LoopIndex_2);

		Position_1 = 17282 * 0;
		unsigned int LoopIndex_3 = InstCount - 0;
		do
		{
			for (unsigned int i = 0; i < 16984; i += 193)
			{
				sub_10041410(FileBufferPointer, Map + 12 * 0x59d, (i + Position_1 + Buffer + 298), 193, dword_451948);
				FileBufferPointer += 121;
			}
			Position_1 += 17282;
			--LoopIndex_3;
		} while (LoopIndex_3);

	return FileBuffer;
}