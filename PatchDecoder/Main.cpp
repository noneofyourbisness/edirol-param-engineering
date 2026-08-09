#include "pch.h"
#include <bitset>;
#include "Encoder.h"

#pragma warning(disable : 4996)

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

u8 dword_4519481[128] = {
0x01,0x00,0x00,0x00,0x03,0x00,0x00,0x00,0x07,0x00,0x00,0x00,0x0f,0x00,0x00,0x00,
0x1f,0x00,0x00,0x00,0x3f,0x00,0x00,0x00,0x7f,0x00,0x00,0x00,0xff,0x00,0x00,0x00,
0xff,0x01,0x00,0x00,0xff,0x03,0x00,0x00,0xff,0x07,0x00,0x00,0xff,0x0f,0x00,0x00,
0xff,0x1f,0x00,0x00,0xff,0x3f,0x00,0x00,0xff,0x7f,0x00,0x00,0xff,0xff,0x00,0x00,
0xff,0xff,0x01,0x00,0xff,0xff,0x03,0x00,0xff,0xff,0x07,0x00,0xff,0xff,0x0f,0x00,
0xff,0xff,0x1f,0x00,0xff,0xff,0x3f,0x00,0xff,0xff,0x7f,0x00,0xff,0xff,0xff,0x00,
0xff,0xff,0xff,0x01,0xff,0xff,0xff,0x03,0xff,0xff,0xff,0x07,0xff,0xff,0xff,0x0f,
0xff,0xff,0xff,0x1f,0xff,0xff,0xff,0x3f,0xff,0xff,0xff,0x7f,0xff,0xff,0xff,0xff
};

int dword_451948[33];


short HexArrayToShort(u8* Array)
{
	short Value = 0;

	memcpy(&Value, Array, 2);

	return Value;
}

int sub_404400(u8* Pointer, u8* Map)
{
	unsigned __int8* MainDataAddress; // esi
	unsigned __int8 Byte; // cl
	int Byte_1; // edi
	int LoopIndex; // eax
	int v6; // ecx
	unsigned int v7; // edx

	MainDataAddress = (*Map + Pointer);
	Byte = *(Map + 2); //Static

	if ((Byte & 128u) != 0)
		Byte = -Byte;

	Byte_1 = Byte; //Static
	LoopIndex = Byte + *(Map + 3); //Static
	v6 = -LoopIndex; //Static
	v7 = 0;

	do
	{
		LoopIndex -= 8;
		v6 += 8;
		v7 = ((*MainDataAddress++) | (v7 << 8));
	} while (LoopIndex > 0);
	int Result = (v7 >> v6) & dword_451948[(Byte_1 - 1)];
	return Result;
}

unsigned int sub_4045C0(u8* a1, u8* a2)
{
	int result; // eax
	unsigned __int16 v3; // cx

	result = sub_404400(a1, a2);
	v3 = a2[4];
	if (a2[8] - v3 < 0 && v3 < 64u)
		result += 64 - v3;
	return result;
}

int sub_4044E0(u8* DataBuffer, u8* DecodeMAP, u8* ResultBuffer, int Size)
{
	int LoopIndex; // ebx
	int v5; // ebp
	int Byte; // eax
	int v10; // ebp
	int i; // [esp+10h] [ebp-4h]
	int Sizea; // [esp+24h] [ebp+10h]

	LoopIndex = Size;
	v5 = 0;

	for (i = 0; LoopIndex > 0; ++i)
	{

		Byte = (signed char)*(DecodeMAP + 2);

		--LoopIndex;
		if (Byte >= 0)
		{
			*ResultBuffer = sub_4045C0(DataBuffer, DecodeMAP);
			ResultBuffer += 1;
		}
		else
		{
			for (Sizea = 0; -Byte < 8; Byte = (signed char)*(DecodeMAP + 2))
			{
				v5 -= Byte;
				*ResultBuffer = sub_404400(DataBuffer, DecodeMAP);
				ResultBuffer += 1;
				DecodeMAP += 12;
				++Sizea;
				if (!LoopIndex--)
					return i;
			}
			v10 = -(Byte + v5);
			if (v10 >= 8)
				return -1;
			*ResultBuffer = (dword_4519481[(v10 - 1) * 4]) & sub_404400(DataBuffer, DecodeMAP);
			ResultBuffer += 1;
			i += Sizea;
		}
		DecodeMAP += 12;
		v5 = 0;
	}
	return i;
}

bool GetBit(u8 Byte, u8 ID)
{
	return (Byte << ID);
}

void SetBit(u8* Byte, u8 ID, bool Bit)
{
	*Byte |= Bit << ID;
}

u8 GetByteByBit(u8* Data, unsigned int BitPosition)
{
	unsigned int RealPosition = BitPosition / 8;
	u8 Shift = BitPosition - RealPosition * 8;
	u8 ShiftByte1 = Shift;
	u8 ShiftByte2 = 8 - Shift;

	return (u8)(Data[RealPosition] >> Shift) | (u8)(Data[RealPosition] << Shift);
}

u8* ConvertEX(u8* Array, unsigned int Size)
{
	u8* ConvertedArray = (u8*)malloc(Size);

	for (int i = 0; i < Size - 1; i++)
	{
		u8 Byte = Array[i] << 1;
		Byte |= (u8)(Array[i + 1] >> 6) << 0;
		ConvertedArray[i] = Byte;
	}

	return ConvertedArray;
}


u8* DecodePatchData(u8* buf, u8* bufPatchInit, u8* bufMap, unsigned int* TotalSize)
{

	int BankCount = buf[0x0];
	int InstCount = BankCount * 256;
	int PatchBufferSize = 948 * InstCount + 4;
	u8* PatchBuffer = (u8*)malloc(PatchBufferSize);
	memset(PatchBuffer, 0, PatchBufferSize);

	for (int i = 0; i < InstCount; i++)
	{
		u8* CurrentPosition = &PatchBuffer[948 * i];
		memcpy(CurrentPosition, &bufPatchInit[0], 79);
		memcpy(CurrentPosition + 79, &bufPatchInit[79], 145);
		memcpy(CurrentPosition + 224, &bufPatchInit[0xe4], 52);
		memcpy(CurrentPosition + 276, &bufPatchInit[0x118], 83);
		memcpy(CurrentPosition + 359, &bufPatchInit[0x16c], 41);
	}

	u8* MainDataAddress = buf + 14;
	u8* MainDataAddress_1 = MainDataAddress;
	u8* MainDataAddress_2 = MainDataAddress;

	unsigned int Position = 0;
	unsigned int Position_1 = 0;
	int LoopIndex_1 = 0;
	bool BoolVar = false;

	for (int i = 0; i < InstCount; i++)
	{
		sub_4044E0(MainDataAddress, bufMap + 12 * 0x242, (Position + PatchBuffer), 79);
		MainDataAddress_1 = MainDataAddress + 56;
		sub_4044E0(MainDataAddress_1, bufMap + 12 * 0x294, (Position + PatchBuffer + 79), 145);
		MainDataAddress_1 += 78;
		sub_4044E0(MainDataAddress_1, bufMap + 12 * 0x328, (Position + PatchBuffer + 224), 52);
		MainDataAddress_1 += 26;
		sub_4044E0(MainDataAddress_1, bufMap + 12 * 0x35D, (Position + PatchBuffer + 276), 83);
		MainDataAddress_1 += 42;
		sub_4044E0(MainDataAddress_1, bufMap + 12 * 0x3B1, (Position + PatchBuffer + 359), 41);
		MainDataAddress = MainDataAddress_1 + 32;
		Position_1 = Position;
		LoopIndex_1 = 4;
		do
		{
			MainDataAddress_2 = (Position_1 + PatchBuffer + 400);
			sub_4044E0(MainDataAddress, bufMap + 12 * 0x3D8 + 36, MainDataAddress_2, 137);
			MainDataAddress += 85;
			BoolVar = LoopIndex_1 == 1;
			Position_1 += 137;
			--LoopIndex_1;
		} while (!BoolVar);
		Position += 948;
	}
	*TotalSize = PatchBufferSize;
	return PatchBuffer;
}

u8* RhythmDecode(u8* RhythmMap, u8* DataBuffer, unsigned int* FinalSize1, unsigned int AddInstSize)
{
	int Offset = 0;
	int Count = DataBuffer[1];
	int Position = 0;

	Count = Count + Offset;

	int FinalSize = 17282 * (Count + AddInstSize) + 4;
	u8* FinalData = (u8*)malloc(FinalSize);

	u8* v26 = DataBuffer + 20;
	u8* v12 = DataBuffer + 20;
	u8* v14 = 0;
	Position = 17282 * Offset;
	int LoopIndex = Count - Offset;
	do
	{
		sub_4044E0(v12, RhythmMap + 12 * 0x46c, (Position + FinalData), 18);
		v14 = (v12 + 14);
		sub_4044E0(v14, RhythmMap + 12 * 0x480, (Position + FinalData + 18), 145);
		v14 += 78;
		sub_4044E0(v14, RhythmMap + 12 * 0x514, (Position + FinalData + 163), 52);
		v14 += 26;
		sub_4044E0(v14, RhythmMap + 12 * 0x549, (Position + FinalData + 215), 83);
		v12 = (v14 + 42);
		for (int i = 0; i < 16984; i += 193)
		{
			unsigned int Aaa = HexArrayToInt(v12);
			int Id = (((Aaa & 0xFF00 | (Aaa << 16)) << 8) | (((Aaa >> 16) | Aaa & 0xFF0000u) >> 8)) - 20;
			sub_4044E0(
				&v26[Id],
				RhythmMap + 12 * 0x59d,
				(Position + i + FinalData + 298),
				193);
			v12 += 4;
		}
		Position += 17282;
		--LoopIndex;
	} while (LoopIndex);

	*FinalSize1 = FinalSize;

	return FinalData;
}

int main()
{

	for (int i = 0; i < 33; i++)
	{
		dword_451948[i] = HexArrayToInt(&dword_4519481[4 * i]);
	}

	const char* filename_in = "RhythmData.bin";
	const char* filename_Map = "MainMap";
	const char* filename_RhythmMap = "RhythmMap";
	const char* filename_PatchInit = "PatchInit";
	const char* filename_out = "Result";
	const char* filename_out1 = "ResultClear";

	FILE* f = fopen(filename_in, "rb");
	if (!f) {
		printf("Error: cannot open %s: %s\n", filename_in,
			strerror(errno));
		return 1;
	}

	fseek(f, 0, SEEK_END);
	size_t fsize = ftell(f);
	fseek(f, 0, SEEK_SET);

	u8* buf = (u8*)malloc(fsize);
	//u8* outbuf = (u8*)malloc(fsize);
	fread(buf, fsize, 1, f);
	fclose(f);


	FILE* MapFile = fopen(filename_Map, "rb");
	if (!MapFile) {
		printf("Error: cannot open %s: %s\n", filename_Map,
			strerror(errno));
		return 1;
	}

	fseek(MapFile, 0, SEEK_END);
	size_t fsizeMap = ftell(MapFile);
	fseek(MapFile, 0, SEEK_SET);

	u8* bufMap = (u8*)malloc(fsizeMap);
	fread(bufMap, fsizeMap, 1, MapFile);
	fclose(MapFile);


	FILE* MapRhythmFile = fopen(filename_RhythmMap, "rb");
	if (!MapRhythmFile) {
		printf("Error: cannot open %s: %s\n", filename_RhythmMap,
			strerror(errno));
		return 1;
	}

	fseek(MapRhythmFile, 0, SEEK_END);
	size_t fsizeRhythmMap = ftell(MapRhythmFile);
	fseek(MapRhythmFile, 0, SEEK_SET);

	u8* bufRhythmMap = (u8*)malloc(fsizeRhythmMap);
	fread(bufRhythmMap, fsizeRhythmMap, 1, MapRhythmFile);
	fclose(MapRhythmFile);


	FILE* MapPatchInit = fopen(filename_Map, "rb");
	if (!MapPatchInit) {
		printf("Error: cannot open %s: %s\n", filename_in,
			strerror(errno));
		return 1;
	}

	fseek(MapPatchInit, 0, SEEK_END);
	size_t fsizePatchInit = ftell(MapPatchInit);
	fseek(MapPatchInit, 0, SEEK_SET);

	u8* bufPatchInit = (u8*)malloc(fsizePatchInit);
	fread(bufPatchInit, fsizePatchInit, 1, MapPatchInit);
	fclose(MapPatchInit);

	unsigned int PatchBufferSize = 574;

	u8* PatchBuffer = (u8*)malloc(574);

	int A = 0;
	int v7 = 0;

	int i = 0;

	int InstCount = 0x1b;

	PatchBufferSize = 574 * InstCount + 14;

	//PatchBuffer = DecodePatchData(buf, bufPatchInit, bufMap, &PatchBufferSize);

	//PatchBufferSize = 574 * InstCount + 14;

	//PatchBuffer = sub_404E50Encode(PatchBuffer, bufMap, 0 , InstCount, dword_451948); PatchBufferSize = 574 * InstCount + 14;
	//PatchBuffer = DecodePatchData(buf, bufPatchInit, bufMap, &PatchBufferSize);

	PatchBuffer = RhythmDecode(bufRhythmMap, buf, &PatchBufferSize, 128 - InstCount);

	// --- write the decoded ("clear") struct data, so you can hex-edit it ---
	FILE* outClear = fopen(filename_out1, "wb");
	if (!outClear) {
		printf("Error: cannot open %s: %s\n", filename_out1, strerror(errno));
		return 1;
	}
	fwrite(PatchBuffer, PatchBufferSize, 1, outClear);
	fclose(outClear);
	// ------------------------------------------------------------------

	// --- reload your hand-edited ResultClear before encoding ---
	FILE* fEdited = fopen(filename_out1, "rb");
	if (!fEdited) {
		printf("Error: cannot open %s: %s\n", filename_out1, strerror(errno));
		return 1;
	}
	fseek(fEdited, 0, SEEK_END);
	size_t editedSize = ftell(fEdited);
	fseek(fEdited, 0, SEEK_SET);

	u8* EditedBuffer = (u8*)malloc(editedSize);
	fread(EditedBuffer, editedSize, 1, fEdited);
	fclose(fEdited);
	// ------------------------------------------------------------

	PatchBuffer = RhythmEncode(EditedBuffer, bufRhythmMap, 0, 128, dword_451948); PatchBufferSize = 11160 * 128 + 20;
	u8* Final = PatchBuffer;//RhythmDecode(bufRhythmMap, PatchBuffer, &PatchBufferSize, false);


	FILE* out = fopen(filename_out, "wb");
	if (!out) {
		printf("Error: cannot open %s: %s\n", filename_out,
			strerror(errno));
		return 1;
	}

	fwrite(Final, 11160 * 128 + 20, 1, out);
	fclose(out);

}