#ifndef md5_h__
#define md5_h__

typedef unsigned char * POINTER_LKY;

typedef unsigned long int UINT4_LKY;

typedef struct {
	UINT4_LKY state[4];                                   /* state (ABCD) */
	UINT4_LKY count[2];        /* number of bits, modulo 2^64 (lsb first) */
	unsigned char buffer[64];                         /* input buffer */
} MD5_CTX_LKY;

void MD5Init_LKY (MD5_CTX_LKY *context);
void MD5Update_LKY (MD5_CTX_LKY *context, unsigned char *input, unsigned int inputLen);
void MD5UpdaterString_LKY(MD5_CTX_LKY *context,const char *string);
int  MD5FileUpdateFile_LKY (MD5_CTX_LKY *context,char *filename);
void MD5Final_LKY (unsigned char digest[16], MD5_CTX_LKY *context);

void MD5String_LKY (char *string,unsigned char digest[16]);
//int  MD5File_LKY (char *filename,unsigned char digest[16]);
int MD5File_LKY (const wchar_t*filename,wchar_t * szOutString);

bool MD5MakeA_LKY(unsigned char * pBuffer , unsigned int nSize ,char	* szOutString, unsigned int nOutLength , bool bLowerCase=false);
bool MD5MakeW_LKY(unsigned char * pBuffer , unsigned int nSize ,wchar_t * szOutString, unsigned int nOutLength , bool bLowerCase=false);

#endif // md5_h__