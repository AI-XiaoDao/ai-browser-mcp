#ifndef FBROWSER_UNITS_H_
#define FBROWSER_UNITS_H_

#include "pch.h"

#include "FBroTypes.h"
#include "FBroBase.h"
#include "FBroMiddleData.h"
#include "FBroString.h"
#include <tchar.h>

inline bool IsNull(const char* buf) {
	return !buf || strlen(buf) == 0;
}

inline bool IsNull(const CefString& buf) {
	return buf.length() == 0;
}

inline bool IsNull(cef_string_t buf) {
	return buf.length == 0;
}

//
//inline std::wstring s2ws(const std::string& s) {
//	int slength = (int)s.length() + 1;
//	int len = MultiByteToWideChar(CP_ACP, 0, s.c_str(), slength, 0, 0);
//	std::unique_ptr<wchar_t[]> buf = std::make_unique<wchar_t[]>(len + 1);
//	MultiByteToWideChar(CP_ACP, 0, s.c_str(), slength, buf.get(), len);
//	return std::wstring(buf.get());
//}

//使用后无需释放
inline std::wstring GetCharToWString(const char* lpSrcBuffer) {
	if (!lpSrcBuffer) return _T("");

	int nSrcLength = (int)strlen(lpSrcBuffer);
	if (nSrcLength > 0) {
		int nDestLength = MultiByteToWideChar(CP_ACP, 0, lpSrcBuffer, nSrcLength, NULL, 0);
		if (nDestLength > 0) {
			std::unique_ptr<wchar_t[]> lpwszDestBuffer = std::make_unique<wchar_t[]>(nDestLength + 1);
			MultiByteToWideChar(CP_ACP, 0, lpSrcBuffer, nSrcLength, lpwszDestBuffer.get(), nDestLength);
			return std::wstring(lpwszDestBuffer.get());
		}
	}

	return _T("");
}

//使用后无需释放
inline CefString GetCharToCefString(const char* lpSrcBuffer) {
	return GetCharToWString(lpSrcBuffer);
}

//并非真正的空，而是返回了带一个字节的结束符
inline char* NullChar() {
	return new char[1]{ '\0' };
}

//使用后需释放
inline char* GetCefStringToChar(const CefString& strValue) {
	if (!strValue.empty()) {

		int nSrcLength = (int)strValue.length();

		if (nSrcLength > 0) {
			int nLength = WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, NULL, 0, NULL, NULL);
			if (nLength > 0) {
				char* pszValue = new char[(size_t)nLength + 1]();
				WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, pszValue, nLength, NULL, NULL);
				return pszValue;
			}
		}
	}
	return NullChar();
}

//并非真正的空，而是返回了带一个字节的结束符
inline std::unique_ptr<char[]> NullUniqueChar() {
	return std::make_unique<char[]>(1);
}

inline std::unique_ptr<char[]> GetCefStringToUniqueChar(const CefString& strValue) {

	if (!strValue.empty())
	{
		int nSrcLength = (int)strValue.length();
		if (nSrcLength > 0) {
			int nLength = WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, NULL, 0, NULL, NULL);
			if (nLength > 0) {
				std::unique_ptr<char[]> pszValue = std::make_unique<char[]>(nLength + 1);
				WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, pszValue.get(), nLength, NULL, NULL);
				return pszValue;
			}
		}
	}
	return NullUniqueChar();
}

inline std::string GetStringMidText(const std::string& indata, const std::string& start, const std::string& end, size_t& find_end_point) {
	size_t point = indata.find(start, find_end_point);
	if (point == std::string::npos) return "";
	point += start.length();
	size_t endpoint = indata.find(end, point + 1);
	if (endpoint == std::string::npos) return "";
	find_end_point = endpoint;
	return indata.substr(point, (size_t)(endpoint - point));
}

inline std::string GetStringMidText(const std::string& indata, const std::string& start, const std::string& end) {
	size_t find_end_point = 0;
	return GetStringMidText(indata, start, end, find_end_point);
}

//查找失败返回std::string::npos
inline size_t FindDataStr(const char* indata, size_t indatasize, const char* findstr, size_t startpoint) {

	if (!indata || !findstr || indatasize == 0)
		return std::string::npos;

	size_t findstrsize = strlen(findstr);
	if (findstrsize == 0) // 空字符串直接返回起始点
		return std::string::npos;

	for (size_t i = startpoint; i < indatasize - findstrsize; i++) {

		if (findstr[0] == indata[i]) {//首字母相等
			bool issame = true;
			for (size_t j = 1; j < findstrsize - 1; j++) {
				if (findstr[j] != indata[i + j]) {
					issame = false;
					break;
				}
			}
			if (issame)
				return i;
		}
	}
	return std::string::npos;
}

inline bool GetMidDataStr(const char* const indata, size_t indatasize, const char* startstr, const char* endstr, HANDLE& retchar, size_t& retlength, size_t& start_point) {

	size_t startpoint = FindDataStr(indata, indatasize, startstr, start_point);
	if (startpoint == std::string::npos) return false;
	size_t endpoint = FindDataStr(indata, indatasize, endstr, startpoint + (int)strlen(startstr));
	if (endpoint == std::string::npos) return false;

	start_point = endpoint;

	retchar = (char*)indata + startpoint + (int)strlen(startstr);
	retlength = endpoint - startpoint - (int)strlen(startstr);
	return true;
}


inline bool GetMidDataStr(const char* const indata, size_t indatasize, const char* startstr, const char* endstr, HANDLE& retchar, size_t& retlength) {
	size_t point = 0;
	return GetMidDataStr(indata, indatasize, startstr, endstr, retchar, retlength, point);
}


inline std::string GetCefStringToString(const CefString& strValue) {
	if (strValue.empty())
		return "";

	int nSrcLength = (int)strValue.length();

	if (nSrcLength <= 0) {
		return "";
	}

	int nLength = WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, NULL, 0, NULL, NULL);
	if (nLength > 0) {
		std::unique_ptr<char[]> buf = std::make_unique<char[]>(nLength + 1);
		WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, buf.get(), nLength, NULL, NULL);
		return std::string(buf.get());
	}
	return "";
};

//retbuf需要分配空间
inline int GetCefStringToChar(const CefString& strValue, char* retbuf, int nSize) {

	if (!strValue.empty()) {
		int nSrcLength = (int)strValue.length();
		if (nSrcLength > 0) {
			if (nSize == 0)
				return WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, NULL, 0, NULL, NULL);
			else {
				WideCharToMultiByte(CP_ACP, 0, (LPCWCH)strValue.c_str(), nSrcLength, retbuf, nSize, NULL, NULL);
				retbuf[nSize] = '\0';
				return nSize;
			}

		}
	}
	return 0;
};

//只能内部使用
inline std::wstring FBroStringToWString(CefRefPtr<FBroString> indata) {
	if (indata) {
		int size = FBroString_WSize(indata);
		if (size > 0) {
			std::unique_ptr<wchar_t[]> buf = std::make_unique<wchar_t[]>((size_t)size + 1);
			FBroString_GetWcharData(indata, buf.get());
			return std::wstring(buf.get());
		}
	}
	return _T("");
};

//时间转换成文本
inline std::string DatetimeToString(time_t intime, const std::string& format = "%04d/%02d/%02d %02d:%02d:%02d") {

	if (intime == 0) return "";

	char szTime[100] = { '\0' };

	std::unique_ptr<tm> pTm(new tm);
	localtime_s(pTm.get(), &intime);

	pTm->tm_year += 1900;
	pTm->tm_mon += 1;

	sprintf_s(szTime, format.c_str(),
		pTm->tm_year, pTm->tm_mon, pTm->tm_mday, pTm->tm_hour, pTm->tm_min, pTm->tm_sec);

	return std::string(szTime);
};

//文本转换成时间
inline time_t StringToDatetime(const std::string& format, const std::string& str) {
	
	int year, month, day, hour, minute, second;// 定义时间的各个int临时变量。
	size_t itemsParsed = sscanf_s(str.c_str(), format.c_str(), &year, &month, &day, &hour, &minute, &second);// 将std::string存储的日期时间，转换为int临时变量。

	if (itemsParsed == 6) {
		tm tm_ = {};
		tm_.tm_year = year - 1900;                 // 年，由于tm结构体存储的是从1900年开始的时间，所以tm_year为int临时变量减去1900。
		tm_.tm_mon = month - 1;                    // 月，由于tm结构体的月份存储范围为0-11，所以tm_mon为int临时变量减去1。
		tm_.tm_mday = day;                         // 日。
		tm_.tm_hour = hour;                        // 时。
		tm_.tm_min = minute;                       // 分。
		tm_.tm_sec = second;                       // 秒。
		tm_.tm_isdst = 0;                          // 非夏令时。
		time_t t_ = mktime(&tm_);                  // 将tm结构体转换成time_t格式。
		return t_;                                 // 返回值。 
	}
	return time_t();
};


//返回最后一个查找到的位置
inline size_t StringReplace(std::string& text, const std::string& searchTerm, const std::string& replacement, size_t start = 0, bool replaceAll = false) {

	size_t ret = 0, pos = start;
	while ((pos = text.find(searchTerm, pos)) != std::string::npos) {
		ret = pos;
		text.replace(pos, searchTerm.length(), replacement);
		pos += replacement.length();
		if (replaceAll == false)
			break;
	}
	return ret;
};


DLLEXPORT bool TEXPORTS ClearWcharData(wchar_t** indata, unsigned int count);


#endif