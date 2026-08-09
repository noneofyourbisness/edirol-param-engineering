
#include "pch.h"
#include <string>
#include <iostream>

#include "EncryptionController.h";

#define LOWBYTE(v)   ((unsigned char) (v))
#define HIGHBYTE(v)  ((unsigned char) (((unsigned int) (v)) >> 8))
#define BYTELOW(v)   (*(((unsigned char *) (&v) + 1)))
#define BYTEHIGH(v)  (*((unsigned char *) (&v)))

#pragma warning(disable : 4996)

typedef unsigned char	u8;
typedef unsigned short	u16;
typedef unsigned int	u32;


int ByteArrayToIntBigEndian(u8* Array);
int ByteArrayToIntLittleEndian(u8* Array);

u8 GetLowSubByte(u8 Byte)
{
	u8 low = Byte & 0x0F;
	return low;
}

u8 GetHighSubByte(u8 Byte)
{
	u8 high = Byte >> 4;
	return high;
}

int IntLittleEndian(int Value)
{
	u8* b = new u8[4];
	memcpy(b, &Value, 4);
	return ByteArrayToIntLittleEndian(b);
}

int IntBigEndian(int Value)
{
	u8* b = new u8[4];
	memcpy(b, &Value, 4);
	return ByteArrayToIntBigEndian(b);
}

int ByteArrayToIntBigEndian(u8* Array)
{
	u8* b = new u8[4];
	b[0] = Array[0];
	b[1] = Array[1];
	b[2] = Array[2];
	b[3] = Array[3];

	int Final = 0;

	memcpy(&Final, b, 4);

	return Final;
}

int ByteArrayToIntLittleEndian(u8* Array)
{
	u8* b = new u8[4];
	b[3] = Array[0];
	b[2] = Array[1];
	b[1] = Array[2];
	b[0] = Array[3];

	int Final = 0;

	memcpy(&Final, b, 4);

	return Final;
}

int ByteArrayToIntSpecial1(u8* Array)
{
	u8* b = new u8[4];
	b[3] = Array[0];
	b[2] = Array[1];
	b[1] = Array[2];
	b[0] = Array[3];

	int Final = 0;

	memcpy(&Final, b, 4);

	return Final;
}

int ByteArrayToIntMidBigEndian(u8* Array)
{
	//BADC
	u8* b = new u8[4];
	b[1] = Array[0];
	b[0] = Array[1];
	b[3] = Array[2];
	b[2] = Array[3];

	int Final = 0;

	memcpy(&Final, b, 4);

	return Final;
}

/*int HexArrayToInt(u8* Array)
{
	int A = 0;
	int* Final = &A;
	Final = (int*)Array;

	return *Final;
}*/

int Decrypt2(u8* Data, int a2, int a3) // BigEndian
{
	Data -= 20;

	int result; // eax

	int Add = 0x1ac;

	switch (a2)
	{
	case 0:
		result = HexArrayToInt(&Data[300]);
		break;
	case 1:
		result = HexArrayToInt(&Data[308]);
		break;
	case 2:
		result = HexArrayToInt(&Data[316]);
		break;
	case 3:
		result = HexArrayToInt(&Data[(8 * a3) + 328]);
		break;
	case 4:
		result = HexArrayToInt(&Data[(8 * a3) + 368]);
		break;
	case 5:
		result = HexArrayToInt(&Data[(8 * a3) + 408]);
		break;
	default:
		result = 0;
		break;
	}
	return result + Add;
}

int Decrypt1(u8* Data, int a2, int a3) // LittleEndian
{
	Data -= 20;

	int result; // eax

	switch (a2)
	{
	case 0:

		result = HexArrayToInt(&Data[304]);
		break;
	case 1:
		result = HexArrayToInt(&Data[312]);
		break;
	case 2:
		result = HexArrayToInt(&Data[320]);
		break;
	case 3:
		result = HexArrayToInt(&Data[(8 * a3) + 332]);
		break;
	case 4:
		result = HexArrayToInt(&Data[(8 * a3) + 372]);
		break;
	case 5:
		result = HexArrayToInt(&Data[(8 * a3) + 412]);
		break;
	default:
		result = 0;
		break;
	}
	return result;
}

/*int SetLowByte(int Value, u8 Byte)
{
	u8* ExtraBytes = (u8*)malloc(4);

	memcpy(ExtraBytes, &Value, 4);

	ExtraBytes[0] = Byte;

	memcpy(&Value, ExtraBytes, 4);

	free(ExtraBytes);

	return Value;
}*/

int SetHighByte(int Value, u8 Byte)
{
	u8* ExtraBytes = (u8*)malloc(4);

	memcpy(ExtraBytes, &Value, 4);

	ExtraBytes[3] = Byte;

	memcpy(&Value, ExtraBytes, 4);

	return Value;
}

int ASize = 1048576;

u8* DecodeArrayAAA(u8* Buffer, unsigned int Position, unsigned int Size)
{
	unsigned int Count = Size >> 20;
	u8* Total = (u8*)malloc(Size);
	int i = 0;

	//for (int i = 0; i < Count; i++)
	{
		u8* BufferClone = (u8*)malloc(Size);
		u8* ExBuffer = (u8*)malloc(Size);

		//int Minari = Size - Position;

		memcpy(BufferClone, &Buffer[Position + ASize * i], Size);
		DecodeArray1(Buffer + 24, BufferClone, 0, ExBuffer, Size);

		memcpy(Total, ExBuffer, Size);
		free(ExBuffer);
		free(BufferClone);
	}

	return Total;
}

u8* EncodeArray1(u8* DecodeMap, u8* Buffer, unsigned int Size)
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

			MoveByte = DecodeMap[var1];
			Byte = Buffer[i];
			ExBuffer[MoveByte + Extra] = Byte;
		}


		memcpy(Total, ExBuffer, Size);
		free(ExBuffer);
	}

	return Total;
}


#define BYTEn(x, n)   (*((u8*)&(x)+n))
#define BYTE1(x)   BYTEn(x,  1)
#define HIBYTE(x)   (*((u8*)&(x)+1))

int ReadFiles(const char* filename_in, const char* outputDir)
{
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

	u8* HeaderPosition = buf; //428 bytes;
	u8* DecodeMapPosition = &buf[24];

	buf = &buf[24];


	unsigned int PatchSize = Decrypt1(HeaderPosition, 1, 0);
	unsigned int PatchAddress = Decrypt2(HeaderPosition, 1, 0);

	unsigned int RhythmSize = Decrypt1(HeaderPosition, 2, 0);
	unsigned int RhythmAddress = Decrypt2(HeaderPosition, 2, 0);

	int Size = 0x100000;

	unsigned int ROMCount = HexArrayToInt(&HeaderPosition[0x130]);
	for (int i = 0; i < ROMCount; i++)
	{
		unsigned int ROMSize = Decrypt1(HeaderPosition, 5, i);
		unsigned int ROMAddress = Decrypt2(HeaderPosition, 5, i);

		unsigned int WaveInitSize = Decrypt1(HeaderPosition, 4, i);
		unsigned int WaveInitAddress = Decrypt2(HeaderPosition, 4, i);

		unsigned int ToneInitSize = Decrypt1(HeaderPosition, 3, i);
		unsigned int ToneInitAddress = Decrypt2(HeaderPosition, 3, i);

		//unsigned int ROMSizeExtra = ROMSize >> 20;

		u8* ROMData = DecodeArrayAAA(HeaderPosition, ROMAddress, ROMSize);
		u8* WaveInitData = DecodeArrayAAA(HeaderPosition, WaveInitAddress, WaveInitSize);
		u8* ToneInitData = DecodeArrayAAA(HeaderPosition, ToneInitAddress, ToneInitSize);

		{
			std::string Path = outputDir;
			Path += "ROMData ";
			Path += std::to_string(i);
			Path += ".bin";

			FILE* out = fopen(Path.c_str(), "wb");
			if (!out) {
				printf("Error: cannot open %s: %s\n", Path.c_str(),
					strerror(errno));
				return 1;
			}

			fwrite(ROMData, ROMSize, 1, out);
			fclose(out);
		}

		{
			std::string Path = outputDir;
			Path += "WaveInitData ";
			Path += std::to_string(i);
			Path += ".bin";

			FILE* out = fopen(Path.c_str(), "wb");
			if (!out) {
				printf("Error: cannot open %s: %s\n", Path.c_str(),
					strerror(errno));
				return 1;
			}

			fwrite(WaveInitData, WaveInitSize, 1, out);
			fclose(out);
		}

		{
			std::string Path = outputDir;
			Path += "ToneInitData ";
			Path += std::to_string(i);
			Path += ".bin";

			FILE* out = fopen(Path.c_str(), "wb");
			if (!out) {
				printf("Error: cannot open %s: %s\n", Path.c_str(),
					strerror(errno));
				return 1;
			}

			fwrite(ToneInitData, ToneInitSize, 1, out);
			fclose(out);
		}
	}

	u8* PatchData = DecodeArrayAAA(HeaderPosition, PatchAddress, PatchSize);
	u8* RhythmData = DecodeArrayAAA(HeaderPosition, RhythmAddress, RhythmSize);

	{
		std::string PatchPath = outputDir; PatchPath += "PatchData.bin";
		FILE* out = fopen(PatchPath.c_str(), "wb");
		if (!out) {
			printf("Error: cannot open %s: %s\n", PatchPath.c_str(),
				strerror(errno));
			return 1;
		}

		fwrite(PatchData, PatchSize, 1, out);
		fclose(out);
	}

	{
		std::string RhythmPath = outputDir; RhythmPath += "RhythmData.bin";
		FILE* out = fopen(RhythmPath.c_str(), "wb");
		if (!out) {
			printf("Error: cannot open %s: %s\n", RhythmPath.c_str(),
				strerror(errno));
			return 1;
		}

		fwrite(RhythmData, RhythmSize, 1, out);
		fclose(out);
	}

	printf("Extraction complete: %u ROM bank(s), Patch=%u bytes, Rhythm=%u bytes\n", ROMCount, PatchSize, RhythmSize);
	return 0;
}

u8* ReadFile(unsigned int* Size, const char* Path)
{

	FILE* f = fopen(Path, "rb");
	if (!f) {
		printf("Error: cannot open %s: %s\n", Path,
			strerror(errno));
		return 0;
	}

	fseek(f, 0, SEEK_END);
	size_t fsize = ftell(f);
	fseek(f, 0, SEEK_SET);

	u8* Corebuf = (u8*)malloc(fsize);
	//u8* outbuf = (u8*)malloc(fsize);
	fread(Corebuf, fsize, 1, f);
	fclose(f);

	*Size = fsize;

	return Corebuf;
}

// Per-bank header field offsets (validated against real multi-bank param.dat files):
//   ToneInit: size @ (8*i)+312, address @ (8*i)+308
//   WaveInit: size @ (8*i)+352, address @ (8*i)+348
//   ROM:      size @ (8*i)+392, address @ (8*i)+388
// All address fields are stored relative to file offset 0x1AC (428).
u8* CreateParamFile(u8* CoreFile, unsigned int CoreFileSize,
	u8* PatchData, unsigned int PatchDataSize,
	u8* RhythmData, unsigned int RhythmDataSize,
	unsigned int ROMCount,
	u8** RomArr, unsigned int* RomSizeArr,
	u8** WaveInitArr, unsigned int* WaveInitSizeArr,
	u8** ToneInitArr, unsigned int* ToneInitSizeArr,
	unsigned int* FinalDataSize)
{
	EncryptionController Encryption = EncryptionController(CoreFile);

	unsigned int Size = 428 + PatchDataSize + RhythmDataSize;
	for (unsigned int i = 0; i < ROMCount; i++)
		Size += RomSizeArr[i] + WaveInitSizeArr[i] + ToneInitSizeArr[i];

	u8* FinalData = (u8*)malloc(Size);

	memcpy(FinalData, CoreFile, 428);

	// keep the header's own ROM bank count in sync in case it was edited
	memcpy(&FinalData[0x130], &ROMCount, 4);

	memcpy(&FinalData[0x124], &PatchDataSize, 4);
	memcpy(&FinalData[0x12c], &RhythmDataSize, 4);

	unsigned int Address = 0;

	memcpy(&FinalData[0x1ac + Address], Encryption.EncodeArray(PatchData, PatchDataSize), PatchDataSize);
	memcpy(&FinalData[0x120], &Address, 4);
	Address += PatchDataSize;

	memcpy(&FinalData[0x1ac + Address], Encryption.EncodeArray(RhythmData, RhythmDataSize), RhythmDataSize);
	memcpy(&FinalData[0x128], &Address, 4);
	Address += RhythmDataSize;

	for (unsigned int i = 0; i < ROMCount; i++)
	{
		unsigned int ToneInitSizeOff = (8 * i) + 312;
		unsigned int ToneInitAddrOff = (8 * i) + 308;
		unsigned int WaveInitSizeOff = (8 * i) + 352;
		unsigned int WaveInitAddrOff = (8 * i) + 348;
		unsigned int RomSizeOff = (8 * i) + 392;
		unsigned int RomAddrOff = (8 * i) + 388;

		memcpy(&FinalData[ToneInitSizeOff], &ToneInitSizeArr[i], 4);
		memcpy(&FinalData[WaveInitSizeOff], &WaveInitSizeArr[i], 4);
		memcpy(&FinalData[RomSizeOff], &RomSizeArr[i], 4);

		memcpy(&FinalData[0x1ac + Address], Encryption.EncodeArray(ToneInitArr[i], ToneInitSizeArr[i]), ToneInitSizeArr[i]);
		memcpy(&FinalData[ToneInitAddrOff], &Address, 4);
		Address += ToneInitSizeArr[i];

		memcpy(&FinalData[0x1ac + Address], Encryption.EncodeArray(WaveInitArr[i], WaveInitSizeArr[i]), WaveInitSizeArr[i]);
		memcpy(&FinalData[WaveInitAddrOff], &Address, 4);
		Address += WaveInitSizeArr[i];

		memcpy(&FinalData[0x1ac + Address], Encryption.EncodeArray(RomArr[i], RomSizeArr[i]), RomSizeArr[i]);
		memcpy(&FinalData[RomAddrOff], &Address, 4);
		Address += RomSizeArr[i];
	}

	*FinalDataSize = Size;

	return FinalData;
}

// Mode 1: extract param.dat into its component .bin files
int RunExtract()
{
	return ReadFiles("C:\\EDIROL\\param.dat", "C:\\EDIROL\\");
}

// Mode 2: reassemble the component .bin files (after you've edited them)
// back into a new, valid param.dat
int RunRebuild()
{
	unsigned int CoreFileSize = 0;
	u8* CoreFileData = ReadFile(&CoreFileSize, "C:\\EDIROL\\param.dat");
	if (!CoreFileData) { printf("Error: could not load original param.dat\n"); return 1; }

	unsigned int PatchDataSize = 0;
	u8* PatchData = ReadFile(&PatchDataSize, "C:\\EDIROL\\PatchData.bin");

	unsigned int RhythmDataSize = 0;
	u8* RhythmData = ReadFile(&RhythmDataSize, "C:\\EDIROL\\RhythmData.bin");

	if (!PatchData || !RhythmData) {
		printf("Error: PatchData.bin/RhythmData.bin missing - run 'extract' first.\n");
		return 1;
	}

	// Read the bank count straight from the original file's header so we
	// pick up however many ROM banks actually exist, instead of assuming 1.
	unsigned int ROMCount = HexArrayToInt(&CoreFileData[0x130]);
	printf("Rebuilding with %u ROM bank(s)\n", ROMCount);

	u8** RomArr = (u8**)malloc(sizeof(u8*) * ROMCount);
	unsigned int* RomSizeArr = (unsigned int*)malloc(sizeof(unsigned int) * ROMCount);
	u8** WaveInitArr = (u8**)malloc(sizeof(u8*) * ROMCount);
	unsigned int* WaveInitSizeArr = (unsigned int*)malloc(sizeof(unsigned int) * ROMCount);
	u8** ToneInitArr = (u8**)malloc(sizeof(u8*) * ROMCount);
	unsigned int* ToneInitSizeArr = (unsigned int*)malloc(sizeof(unsigned int) * ROMCount);

	for (unsigned int i = 0; i < ROMCount; i++)
	{
		std::string romPath = "C:\\EDIROL\\ROMData " + std::to_string(i) + ".bin";
		std::string waveInitPath = "C:\\EDIROL\\WaveInitData " + std::to_string(i) + ".bin";
		std::string toneInitPath = "C:\\EDIROL\\ToneInitData " + std::to_string(i) + ".bin";

		RomArr[i] = ReadFile(&RomSizeArr[i], romPath.c_str());
		WaveInitArr[i] = ReadFile(&WaveInitSizeArr[i], waveInitPath.c_str());
		ToneInitArr[i] = ReadFile(&ToneInitSizeArr[i], toneInitPath.c_str());

		if (!RomArr[i] || !WaveInitArr[i] || !ToneInitArr[i]) {
			printf("Error: missing bank %u files - run 'extract' first, or check bank count.\n", i);
			return 1;
		}
	}

	unsigned int FinalDataSize = 0;
	u8* FinalData = CreateParamFile(CoreFileData, CoreFileSize, PatchData, PatchDataSize,
		RhythmData, RhythmDataSize, ROMCount, RomArr, RomSizeArr,
		WaveInitArr, WaveInitSizeArr, ToneInitArr, ToneInitSizeArr, &FinalDataSize);

	FILE* out = fopen("C:\\EDIROL\\ParamResult.dat", "wb");
	if (!out) {
		printf("Error: cannot open %s: %s\n", "C:\\EDIROL\\ParamResult.dat",
			strerror(errno));
		return 1;
	}

	fwrite(FinalData, FinalDataSize, 1, out);
	fclose(out);

	printf("Rebuild complete: wrote %u bytes to C:\\EDIROL\\ParamResult.dat\n", FinalDataSize);
	return 0;
}

int main(int argc, char** argv)
{
	// Usage: RomCreator.exe extract    -> splits C:\EDIROL\param.dat into .bin files
	//        RomCreator.exe rebuild    -> reassembles the .bin files into ParamResult.dat
	if (argc < 2) {
		printf("Usage: %s [extract|rebuild]\n", argv[0]);
		return 1;
	}

	if (strcmp(argv[1], "extract") == 0)
		return RunExtract();
	else if (strcmp(argv[1], "rebuild") == 0)
		return RunRebuild();

	printf("Unknown mode '%s'. Use 'extract' or 'rebuild'.\n", argv[1]);
	return 1;
}