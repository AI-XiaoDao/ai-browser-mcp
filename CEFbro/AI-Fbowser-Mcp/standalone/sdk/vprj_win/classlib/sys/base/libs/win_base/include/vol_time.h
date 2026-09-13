
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_TIME_FUNCTIONS_H__
#define __VOL_TIME_FUNCTIONS_H__

class CVolString;

// 获得计算机或程序启动后已经经过的Tick数目
DWORD MGetTickCount ();

// 获得从UTC 1/1/1970到当前时间的时间段长度
timeval MGetTimeOfDay ();

// 规范化指定的timeval
void NormalizeTimeval (timeval* ptv);

// 返回ptv是否为规范化模式
BOOL_P IsTimevalNormalize (const timeval* ptv);

// 返回本机系统所处时区
INT_P MGetTimeZone ();

// 返回所指定月份拥有的天数
INT_P GetDaysOfMonth (const INT_P npYear, const INT_P npMonth);

// 将所指定的日期时间值转换到文本格式存放到strDateTime中后返回,成功返回对应的日期时间文本,失败返回空文本.
//   npConvertPart: 提供具体的转换部分: 0:全部转换; 1:日期部分; 2:时间部分
//   blpCnFormat: 是否使用中文格式
const TCHAR* DateTimeToStr (const DOUBLE dbDate, CVolString& strDateTime, const INT_P npConvertPart, const BOOL_P blpCnFormat);

// 将所指定的日期时间文本转换到日期时间值后返回,成功返回对应的日期时间值,失败返回 _VOL_MIN_DATE .
//   blpCnFormat: 所提供的日期时间文本是否为中文格式
DOUBLE StrToDateTime (const TCHAR* szDateTimeText, const BOOL_P blpCnFormat);

// 增减时间
//   dbDate: 所欲操作的时间
//   npTimeField: 所增减的时间字段类型: 0:年份; 1:季度; 2:月份; 3:周; 4:日; 5:小时; 6:分钟; 7:秒
DOUBLE TimeChange (DOUBLE dbDate, const INT_P npTimeField, INT64 n64AddValue);

// 将所指定的时间转换到DATE后返回,如果失败则返回dbDateFailed.
DOUBLE ToDate (INT_P npYear, INT_P npMonth, INT_P npDay, INT_P npHour, INT_P npMinute, INT_P npSecond, INT_P npMillSecond, const DOUBLE dbDateFailed);

// 返回"时间1"减去"时间2"之后的间隔数目.
//   npTimeField: 所增减的时间字段类型: 0:年份; 1:季度; 2:月份; 3:周; 4:日; 5:小时; 6:分钟; 7:秒
DOUBLE GetTimeDiff (DOUBLE dbDate1, DOUBLE dbDate2, const INT_P npTimeField);

// 返回一个包含已知时间指定部分的值
//   npTimePartType: 欲取的时间部分: 0:年份; 1:季度; 2:月份; 3:自年首周数; 4:日; 5:小时; 6:分钟; 7:秒; 8:星期几; 9:自年首天数
INT_P GetTimePart (DOUBLE dbDate, const INT_P npTimePartType);

// 返回当前系统日期及时间
DOUBLE GetCurrentDateTime ();

// 设置当前系统日期及时间,返回是否成功.
BOOL_P SetCurrentDateTime (const DOUBLE dbDate);

// 返回一个日期时间型数据的日期部分,其小时/分钟/秒被固定设置为0时0分0秒.
DOUBLE GetDatePart (DOUBLE dbDate);

// 返回一个日期时间型数据的时间部分,其年/月/日被固定设置为2000年1月1日.
DOUBLE GetTimePart (DOUBLE dbDate);

// 返回基于一个过去特定基准时间(北京时间 2017/7/5 15:55)的已经经过的秒数,必定大于等于0.
INT GetSecondsFromMyBaseTime ();

// 将所指定的文件时间转换为日期时间值,如失败则返回_VOL_MIN_DATE.
DOUBLE ConvertFileTime (const FILETIME ftConvert);

#endif
