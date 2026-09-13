
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

#ifndef _PF_WINDOWS

static time_t sGetSecondsSinceEpoch ()
{
    struct timeval tv;
    gettimeofday (&tv, NULL);
    return tv.tv_sec;
}

#endif

DWORD MGetTickCount ()
{
#ifdef _PF_WINDOWS
    return ::GetTickCount ();
#else
    static time_t s_tvSecondsSinceEpoch = sGetSecondsSinceEpoch ();

    struct timeval tv;
    gettimeofday (&tv, NULL);
    ASSERT (tv.tv_sec >= s_tvSecondsSinceEpoch && tv.tv_usec >= 0);

    return (DWORD)((tv.tv_sec - s_tvSecondsSinceEpoch) * 1000 + tv.tv_usec / 1000);
#endif
}

timeval MGetTimeOfDay ()
{
    timeval tv;

#if defined (_PF_WINDOWS)
    FILETIME tfile;
    ::GetSystemTimeAsFileTime (&tfile);

    ULARGE_INTEGER _100ns;
    _100ns.LowPart = tfile.dwLowDateTime;
    _100ns.HighPart = tfile.dwHighDateTime;
    ASSERT (_100ns.QuadPart >= 0x19db1ded53e8000ui64);
    _100ns.QuadPart -= 0x19db1ded53e8000ui64;  // FILETIME是从1/1/1601开始的,将其转换到1/1/1970.

    // FILETIME以100纳秒为单位,将其转换到秒+微秒.
    // 单位换算: 1纳秒 = 十亿分之一秒;  1微秒 = 百万分之一秒
    tv.tv_sec = (long)(_100ns.QuadPart / (NUM_USECS_OF_SECOND * 10));  // 计算秒
    tv.tv_usec = (_100ns.QuadPart % (NUM_USECS_OF_SECOND * 10)) / 10;  // 计算微秒
    ASSERT (IsTimevalNormalize (&tv));
    return tv;
#elif defined (_PF_LINUX)
    VERIFY_EQUAL (::gettimeofday (&tv, NULL), 0);
    // NormalizeTimeval (&tv);
    ASSERT (IsTimevalNormalize (&tv));
    return tv;
#endif
}

void NormalizeTimeval (timeval* ptv)
{
    ASSERT_RW_DATA (ptv);

    // 确保ptv->tv_usec在-NUM_USECS_OF_SECOND到NUM_USECS_OF_SECOND之间
    if (ptv->tv_usec >= NUM_USECS_OF_SECOND)
    {
        do
        {
            ptv->tv_sec++;
            ptv->tv_usec -= NUM_USECS_OF_SECOND;
        }
        while (ptv->tv_usec >= NUM_USECS_OF_SECOND);
    }
    else if (ptv->tv_usec <= -NUM_USECS_OF_SECOND)
    {
        do
        {
            ptv->tv_sec--;
            ptv->tv_usec += NUM_USECS_OF_SECOND;
        }
        while (ptv->tv_usec <= -NUM_USECS_OF_SECOND);
    }
    ASSERT (ptv->tv_usec > -NUM_USECS_OF_SECOND && ptv->tv_usec < NUM_USECS_OF_SECOND);

    // 确保ptv->tv_sec与ptv->tv_usec的符号方向一致
    if (ptv->tv_sec > 0 && ptv->tv_usec < 0)
    {
        ptv->tv_sec--;  // >= 0
        ptv->tv_usec += NUM_USECS_OF_SECOND;  // > 0
    }
    else if (ptv->tv_sec < 0 && ptv->tv_usec > 0)
    {
        ptv->tv_sec++;  // <= 0
        ptv->tv_usec -= NUM_USECS_OF_SECOND;  // < 0
    }
}

BOOL_P IsTimevalNormalize (const timeval* ptv)
{
    ASSERT_RW_DATA (ptv);

    return !(ptv->tv_usec <= -NUM_USECS_OF_SECOND ||
            ptv->tv_usec >= NUM_USECS_OF_SECOND ||
            (ptv->tv_sec > 0 && ptv->tv_usec < 0) ||
            (ptv->tv_sec < 0 && ptv->tv_usec > 0));
}

INT_P MGetTimeZone ()
{
    time_t tm = time (NULL);

    const INT_P npLocalHour = localtime (&tm)->tm_hour;
    return npLocalHour - gmtime (&tm)->tm_hour;
}

const TCHAR* DateTimeToStr (const DOUBLE dbDate, CVolString& strDateTime, const INT_P npConvertPart, const BOOL_P blpCnFormat)
{
    strDateTime.Empty ();

    SYSTEMTIME st;
    ZERO_MEM (&st, sizeof (SYSTEMTIME));

    if (dbDate >= _VOL_MIN_DATE && dbDate <= _VOL_MAX_DATE &&
            ::VariantTimeToSystemTime (dbDate, &st))
    {
        const INT nYear = st.wYear;
        const INT nMonth = st.wMonth;
        const INT nDay = st.wDay;
        const INT nHour = st.wHour;
        const INT nMinute = st.wMinute;
        const INT nSecond = st.wSecond;

        if (blpCnFormat)
        {
            if (npConvertPart == 0 || npConvertPart == 1)  // 全部转换 / 日期部分
                strDateTime.Format (_T ("%d年%d月%d日"), nYear, nMonth, nDay);

            if (npConvertPart == 0 || npConvertPart == 2)  // 全部转换 / 时间部分
            {
                TCHAR buf [64];
                if (nSecond != 0)
                {
                    wsprintf (buf, _T ("%d时%d分%d秒"), nHour, nMinute, nSecond);
                    strDateTime.AddText (buf);
                }
                else if (nMinute != 0)
                {
                    wsprintf (buf, _T ("%d时%d分"), nHour, nMinute);
                    strDateTime.AddText (buf);
                }
                else if (nHour != 0)
                {
                    wsprintf (buf, _T ("%d时"), nHour);
                    strDateTime.AddText (buf);
                }
            }
        }
        else
        {
            if (npConvertPart == 0 || npConvertPart == 1)  // 全部转换 / 日期部分
                strDateTime.Format (_T ("%d/%d/%d"), nMonth, nDay, nYear);

            if (npConvertPart == 0 || npConvertPart == 2)  // 全部转换 / 时间部分
            {
                TCHAR buf [64];
                if (nSecond != 0)
                {
                    wsprintf (buf, (npConvertPart == 0 ? _T (" %d:%d:%d") : _T ("%d:%d:%d")), nHour, nMinute, nSecond);
                    strDateTime.AddText (buf);
                }
                else if (nMinute != 0)
                {
                    wsprintf (buf, (npConvertPart == 0 ? _T (" %d:%d") : _T ("%d:%d")), nHour, nMinute);
                    strDateTime.AddText (buf);
                }
                else if (nHour != 0)
                {
                    wsprintf (buf, (npConvertPart == 0 ? _T (" %d") : _T ("%d")), nHour);
                    strDateTime.AddText (buf);
                }
            }
        }
    }

    return strDateTime.GetText ();
}

DOUBLE StrToDateTime (const TCHAR* szDateTimeText, const BOOL_P blpCnFormat)
{
    if (IsEmptyStr (szDateTimeText))
        return _VOL_MIN_DATE;

    const TCHAR* ps = szDateTimeText;

    TCHAR ch;
    INT_P npIndex;
    INT_P npYear = 0;
    INT_P npMonth = 0;
    INT_P npDay = 0;

    if (blpCnFormat)
    {
        for (npIndex = 0; npIndex <= 3; npIndex++)
        {
            ch = *ps;
            if (ch == 0 || ch < '0' || ch > '9')
                break;
            ps++;
            npYear = npYear * 10 + ch - '0';
        }
        ch = *ps;
        if (ch == '/' || ch == '-' || ch == ':' || ch == '.' || ch == _T ('年'))
            ps++;

        for (npIndex = 0; npIndex <= 1; npIndex++)
        {
            ch = *ps;
            if (ch == 0 || ch < '0' || ch > '9')
                break;
            ps++;
            npMonth = npMonth * 10 + ch - '0';
        }
        ch = *ps;
        if (ch == '/' || ch == '-' || ch == ':' || ch == '.' || ch == _T ('月'))
            ps++;

        for (npIndex = 0; npIndex <= 1; npIndex++)
        {
            ch = *ps;
            if (ch == 0 || ch < '0' || ch > '9')
                break;
            ps++;
            npDay = npDay * 10 + ch - '0';
        }
        ch = *ps;
        if (ch == '/' || ch == '-' || ch == ':' || ch == '.' || ch == ' ' || ch == _T ('日'))
            ps++;
    }
    else
    {
        for (npIndex = 0; npIndex <= 1; npIndex++)
        {
            ch = *ps;
            if (ch == 0 || ch < '0' || ch > '9')
                break;
            ps++;
            npMonth = npMonth * 10 + ch - '0';
        }
        ch = *ps;
        if (ch == '/' || ch == '-' || ch == ':' || ch == '.')
            ps++;

        for (npIndex = 0; npIndex <= 1; npIndex++)
        {
            ch = *ps;
            if (ch == 0 || ch < '0' || ch > '9')
                break;
            ps++;
            npDay = npDay * 10 + ch - '0';
        }
        ch = *ps;
        if (ch == '/' || ch == '-' || ch == ':' || ch == '.')
            ps++;

        for (npIndex = 0; npIndex <= 3; npIndex++)
        {
            ch = *ps;
            if (ch == 0 || ch < '0' || ch > '9')
                break;
            ps++;
            npYear = npYear * 10 + ch - '0';
        }
        ch = *ps;
        if (ch == '/' || ch == '-' || ch == ':' || ch == '.' || ch == ' ')
            ps++;
    }

    //---------------------------------------------------------------------------------

    INT_P npHour = 0;
    for (npIndex = 0; npIndex <= 1; npIndex++)
    {
        ch = *ps;
        if (ch == 0 || ch < '0' || ch > '9')
            break;
        ps++;
        npHour = npHour * 10 + ch - '0';
    }
    ch = *ps;
    if (ch == '/' || ch == '-' || ch == ':' || ch == '.' || (blpCnFormat && ch == _T ('时')))
        ps++;

    INT_P npMinute = 0;
    for (npIndex = 0; npIndex <= 1; npIndex++)
    {
        ch = *ps;
        if (ch == 0 || ch < '0' || ch > '9')
            break;
        ps++;
        npMinute = npMinute * 10 + ch - '0';
    }
    ch = *ps;
    if (ch == '/' || ch == '-' || ch == ':' || ch == '.' || (blpCnFormat && ch == _T ('分')))
        ps++;

    INT_P npSecond = 0;
    for (npIndex = 0; npIndex <= 1; npIndex++)
    {
        ch = *ps;
        if (ch == 0 || ch < '0' || ch > '9')
            break;
        ps++;
        npSecond = npSecond * 10 + ch - '0';
    }
    ch = *ps;
    if (ch != 0 && (blpCnFormat == FALSE || ch != _T ('秒')))
        return _VOL_MIN_DATE;

    return ToDate (npYear, npMonth, npDay, npHour, npMinute, npSecond, 0, _VOL_MIN_DATE);
}

INT_P GetDaysOfMonth (const INT_P npYear, const INT_P npMonth)
{
    static INT_P s_anpMonthDays [12] =
    {
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    };

    INT_P npDays = 0;
    if (npYear >= 100 && npYear <= 9999 && npMonth >= 1 && npMonth <= 12)
    {
        npDays = s_anpMonthDays [npMonth - 1];
        if (npMonth == 2 &&
                ((npYear % 4) == 0 && (npYear % 100) != 0 || (npYear % 400) == 0))  // 是否为闰年?
        {
            npDays = 29;
        }
    }

    return npDays;
}

DOUBLE ToDate (INT_P npYear, INT_P npMonth, INT_P npDay, INT_P npHour, INT_P npMinute, INT_P npSecond, INT_P npMillSecond, const DOUBLE dbDateFailed)
{
    npYear = CLIP (npYear, 100, 9999);
    npMonth = CLIP (npMonth, 1, 12);
    npDay = CLIP (npDay, 1, 31);
    npHour = CLIP (npHour, 0, 23);
    npMinute = CLIP (npMinute, 0, 59);
    npSecond = CLIP (npSecond, 0, 59);
    npMillSecond = CLIP (npMillSecond, 0, 999);

    const INT_P npDaysOfMonth = GetDaysOfMonth (npYear, npMonth);
    npDay = MIN (npDaysOfMonth, npDay);

    //---------------------------------------------------------------------------------

    SYSTEMTIME st;
    ZERO_MEM (&st, sizeof (SYSTEMTIME));
    st.wYear = (WORD)npYear;
    st.wMonth = (WORD)npMonth;
    st.wDay = (WORD)npDay;
    st.wHour = (WORD)npHour;
    st.wMinute = (WORD)npMinute;
    st.wSecond = (WORD)npSecond;
    st.wMilliseconds = 0;  // SystemTimeToVariantTime没有处理毫秒字段

    DOUBLE dbDate;
    if (::SystemTimeToVariantTime (&st, &dbDate) == FALSE)
        return dbDateFailed;

    return dbDate + (DOUBLE)npMillSecond / (1000.0 * 60.0 * 60.0 * 24.0);  // 手动将毫秒字段添加进去

    /*if (::SystemTimeToVariantTime (&st, &dbDate) == FALSE)
        return dbDateFailed;

    ZERO_MEM (&st, sizeof (SYSTEMTIME));
    if (::VariantTimeToSystemTime (dbDate, &st) == FALSE)
        return dbDateFailed;

    return (((INT_P)st.wYear == npYear &&
            (INT_P)st.wMonth == npMonth &&
            (INT_P)st.wDay == npDay &&
            (INT_P)st.wHour == npHour &&
            (INT_P)st.wMinute == npMinute &&
            (INT_P)st.wSecond == npSecond) ? dbDate : dbDateFailed); */
}

static DOUBLE sGetDateTimeSpan (INT_P npDays, INT_P npHours, INT_P npMins, INT_P npSecs, INT64 n64MillSecs)
{
    const DOUBLE dbSpan = (DOUBLE)npDays + ((DOUBLE)npHours) / 24 + ((DOUBLE)npMins) / (24 * 60) + ((DOUBLE)npSecs) / (24 * 60 * 60) + ((DOUBLE)n64MillSecs) / (24.0 * 60.0 * 60.0 * 1000.0);
    #define _MAX_DAYS_IN_SPAN  3615897
    return CLIP (dbSpan, -_MAX_DAYS_IN_SPAN, _MAX_DAYS_IN_SPAN);
}

#define _DATETIME_HALFSECOND  (1.0 / (2.0 * (60.0 * 60.0 * 24.0)))

static DOUBLE sGetSpanTotalDays (const DOUBLE dbDateTimeSpan)
{
    return (DOUBLE)LONGLONG (dbDateTimeSpan + (dbDateTimeSpan < 0 ? -_DATETIME_HALFSECOND : _DATETIME_HALFSECOND));
}

static DOUBLE sGetSpanTotalHours (const DOUBLE dbDateTimeSpan)
{
    return (DOUBLE)LONGLONG ((dbDateTimeSpan + (dbDateTimeSpan < 0 ? -_DATETIME_HALFSECOND : _DATETIME_HALFSECOND)) * 24);
}

static DOUBLE sGetSpanTotalMinutes (const DOUBLE dbDateTimeSpan)
{
    return (DOUBLE)LONGLONG ((dbDateTimeSpan + (dbDateTimeSpan < 0 ? -_DATETIME_HALFSECOND : _DATETIME_HALFSECOND)) * (24 * 60));
}

static DOUBLE sGetSpanTotalSeconds (const DOUBLE dbDateTimeSpan)
{
    return (DOUBLE)LONGLONG ((dbDateTimeSpan + (dbDateTimeSpan < 0 ? -_DATETIME_HALFSECOND : _DATETIME_HALFSECOND)) * (24 * 60 * 60));
}

static DOUBLE sGetSpanTotalMillSeconds (const DOUBLE dbDateTimeSpan)
{
    return (DOUBLE)LONGLONG (dbDateTimeSpan * 24.0 * 60.0 * 60.0 * 1000.0 + 0.5);
}

static DOUBLE sDoubleFromDate (DOUBLE date)
{    
    if (date > -_DATETIME_HALFSECOND)
        return date;

    const DOUBLE db = ceil (date);
    return db - (date - db);
}

static DOUBLE sDateFromDouble (DOUBLE f)
{    
    if (f > -_DATETIME_HALFSECOND)
        return f;

    const DOUBLE dbTemp = floor (f);
    return dbTemp + (dbTemp - f);
}

static DOUBLE sAddDateTime (const DOUBLE dbDate, const INT_P npDays, const INT_P npHours, const INT_P npMins, const INT_P npSecs, INT64 n64MillSecs)
{
    return sDateFromDouble (sDoubleFromDate (dbDate) + sGetDateTimeSpan (npDays, npHours, npMins, npSecs, n64MillSecs));
}

static DOUBLE sSubDateTime (const DOUBLE dbDate, const INT_P npDays, const INT_P npHours, const INT_P npMins, const INT_P npSecs, INT64 n64MillSecs)
{
    return sDateFromDouble (sDoubleFromDate (dbDate) - sGetDateTimeSpan (npDays, npHours, npMins, npSecs, n64MillSecs));
}

DOUBLE TimeChange (DOUBLE dbDate, const INT_P npTimeField, INT64 n64AddValue)
{
    dbDate = CLIP (dbDate, _VOL_MIN_DATE, _VOL_MAX_DATE);

    if (n64AddValue != 0)
    {
        if (npTimeField < 3)
        {
            SYSTEMTIME st = { 0 };
            if (::VariantTimeToSystemTime (dbDate, &st) == FALSE)
                return dbDate;

            INT_P npYear = (INT_P)(UINT_P)st.wYear;
            INT_P npMonth = (INT_P)(UINT_P)st.wMonth;
            INT_P npDay = (INT_P)(UINT_P)st.wDay;
            INT_P npHour = (INT_P)(UINT_P)st.wHour;
            INT_P npMinute = (INT_P)(UINT_P)st.wMinute;
            INT_P npSecond = (INT_P)(UINT_P)st.wSecond;
            INT_P npMillSecond = (INT_P)(UINT_P)st.wMilliseconds;

            switch (npTimeField)
            {
            case 0:  // 年份
                dbDate = ToDate (npYear + (INT_P)n64AddValue, npMonth, npDay, npHour, npMinute, npSecond, npMillSecond, dbDate);
                break;

            case 1:  // 季度
                n64AddValue *= 3;
            case 2:  // 月份
                npMonth += (INT_P)n64AddValue;
                while (TRUE)
                {
                    if (npMonth < 1)
                    {
                        npYear--;
                        npMonth += 12;
                    }
                    else if (npMonth > 12)
                    {
                        npYear++;
                        npMonth -= 12;
                    }
                    else
                        break;
                }
                dbDate = ToDate (npYear, npMonth, npDay, npHour, npMinute, npSecond, npMillSecond, dbDate);
                break;

            DEFAULT_FAIL
            }
        }
        else
        {
            switch (npTimeField)
            {
            case 3:  // 周
                n64AddValue *= 7;
            case 4:  // 日
                if (n64AddValue >= 0)
                    dbDate = sAddDateTime (dbDate, (INT_P)n64AddValue, 0, 0, 0, 0);
                else
                    dbDate = sSubDateTime (dbDate, -(INT_P)n64AddValue, 0, 0, 0, 0);
                break;
            case 5:  // 小时
                if (n64AddValue >= 0)
                    dbDate = sAddDateTime (dbDate, 0, (INT_P)n64AddValue, 0, 0, 0);
                else
                    dbDate = sSubDateTime (dbDate, 0, -(INT_P)n64AddValue, 0, 0, 0);
                break;
            case 6:  // 分钟
                if (n64AddValue >= 0)
                    dbDate = sAddDateTime (dbDate, 0, 0, (INT_P)n64AddValue, 0, 0);
                else
                    dbDate = sSubDateTime (dbDate, 0, 0, -(INT_P)n64AddValue, 0, 0);
                break;
            case 7:  // 秒
                if (n64AddValue >= 0)
                    dbDate = sAddDateTime (dbDate, 0, 0, 0, (INT_P)n64AddValue, 0);
                else
                    dbDate = sSubDateTime (dbDate, 0, 0, 0, -(INT_P)n64AddValue, 0);
                break;
            case 8:  // 毫秒
                if (n64AddValue >= 0)
                    dbDate = sAddDateTime (dbDate, 0, 0, 0, 0, n64AddValue);
                else
                    dbDate = sSubDateTime (dbDate, 0, 0, 0, 0, -n64AddValue);
                break;
            DEFAULT_FAIL
            }
        }
    }

    return dbDate;
}

DOUBLE GetTimeDiff (DOUBLE dbDate1, DOUBLE dbDate2, const INT_P npTimeField)
{
    dbDate1 = CLIP (dbDate1, _VOL_MIN_DATE, _VOL_MAX_DATE);
    dbDate2 = CLIP (dbDate2, _VOL_MIN_DATE, _VOL_MAX_DATE);

    DOUBLE dbDiff = 0;
    while (dbDate1 != dbDate2)
    {
        SYSTEMTIME st1 = { 0 };
        SYSTEMTIME st2 = { 0 };

        if (npTimeField <= 3)
        {
            if (::VariantTimeToSystemTime (dbDate1, &st1) == FALSE ||
                    ::VariantTimeToSystemTime (dbDate2, &st2) == FALSE)
            {
                break;
            }
        }

        if (npTimeField < 3)
        {
            switch (npTimeField)
            {
            case 0:  // 年份
                dbDiff = (DOUBLE)((INT_P)(UINT_P)st1.wYear - (INT_P)(UINT_P)st2.wYear);
                break;
            case 1:  // 季度
                dbDiff = (DOUBLE)(((INT_P)(UINT_P)st1.wYear - (INT_P)(UINT_P)st2.wYear) * 4 +
                        ((INT_P)(UINT_P)st1.wMonth - 1) / 3 - ((INT_P)(UINT_P)st2.wMonth - 1) / 3);
                break;
            case 2:  // 月份
                dbDiff = (DOUBLE)(((INT_P)(UINT_P)st1.wYear - (INT_P)(UINT_P)st2.wYear) * 12 +
                        (INT_P)(UINT_P)st1.wMonth - (INT_P)(UINT_P)st2.wMonth);
                break;
            }
        }
        else
        {
            dbDate1 = sDoubleFromDate (dbDate1);
            dbDate2 = sDoubleFromDate (dbDate2);

            DOUBLE dbSpan = dbDate1 - dbDate2;
            dbSpan = CLIP (dbSpan, -_MAX_DAYS_IN_SPAN, _MAX_DAYS_IN_SPAN);

            switch (npTimeField)
            {
            case 3:  // 周
                dbDiff = (DOUBLE)(INT)((INT)sGetSpanTotalDays (dbSpan) / 7);
                if (dbDate1 > dbDate2 && st1.wDayOfWeek < st2.wDayOfWeek)
                    dbDiff = dbDiff + 1;
                else if (dbDate1 < dbDate2 && st2.wDayOfWeek < st1.wDayOfWeek)
                    dbDiff = dbDiff - 1;
                break;
            case 4:  // 日
                dbDiff = sGetSpanTotalDays (dbSpan);
                break;
            case 5:  // 小时
                dbDiff = sGetSpanTotalHours (dbSpan);
                break;
            case 6:  // 分钟
                dbDiff = sGetSpanTotalMinutes (dbSpan);
                break;
            case 7:  // 秒
                dbDiff = sGetSpanTotalSeconds (dbSpan);
                break;
            case 8:  // 毫秒
                dbDiff = sGetSpanTotalMillSeconds (dbSpan);
                break;
            }
        }

        break;
    }

    return dbDiff;
}

INT_P GetTimePart (DOUBLE dbDate, const INT_P npTimePartType)
{
    dbDate = CLIP (dbDate, _VOL_MIN_DATE, _VOL_MAX_DATE);

    SYSTEMTIME st = { 0 };
    if (::VariantTimeToSystemTime (dbDate, &st))
    {
        switch (npTimePartType)
        {
        case 0:  // 年份
            return (INT_P)(UINT_P)st.wYear;

        case 1:  // 季度
            return (INT_P)(UINT_P)(st.wMonth - 1) / 3 + 1;

        case 2:  // 月份
            return (INT_P)(UINT_P)st.wMonth;

        case 4:  // 日
            return (INT_P)(UINT_P)st.wDay;

        case 5:  // 小时
            return (INT_P)(UINT_P)st.wHour;

        case 6:  // 分钟
            return (INT_P)(UINT_P)st.wMinute;

        case 7:  // 秒
            return (INT_P)(UINT_P)st.wSecond;

        case 8:  // 星期几
            return (INT_P)(UINT_P)st.wDayOfWeek + 1;

        case 3:  // 自年首周数
        case 9:  {  // 自年首天数
            UDATE udate = { 0 };
            if (SUCCEEDED (::VarUdateFromDate (dbDate, 0, &udate)))
                return (npTimePartType == 3 ? ((INT_P)(UINT_P)udate.wDayOfYear - 1) / 7 + 1 : (INT_P)(UINT_P)udate.wDayOfYear);
            break;  }

        DEFAULT_FAIL
        }
    }

    return -1;
}

DOUBLE GetCurrentDateTime ()
{
    SYSTEMTIME st;
    ::GetLocalTime (&st);

    return ToDate ((INT_P)(UINT_P)st.wYear, (INT_P)(UINT_P)st.wMonth, (INT_P)(UINT_P)st.wDay, (INT_P)(UINT_P)st.wHour, (INT_P)(UINT_P)st.wMinute, (INT_P)(UINT_P)st.wSecond, (INT_P)(UINT_P)st.wMilliseconds, _VOL_MIN_DATE);
}

BOOL_P SetCurrentDateTime (const DOUBLE dbDate)
{
	SYSTEMTIME sysTime;
    return (VariantTimeToSystemTime (CLIP (dbDate, _VOL_MIN_DATE, _VOL_MAX_DATE), &sysTime) && ::SetLocalTime (&sysTime));
}

DOUBLE GetDatePart (DOUBLE dbDate)
{
    dbDate = CLIP (dbDate, _VOL_MIN_DATE, _VOL_MAX_DATE);

    SYSTEMTIME st = { 0 };
    if (::VariantTimeToSystemTime (dbDate, &st))
        dbDate = ToDate ((INT_P)(UINT_P)st.wYear, (INT_P)(UINT_P)st.wMonth, (INT_P)(UINT_P)st.wDay, 0, 0, 0, 0, dbDate);

    return dbDate;
}

DOUBLE GetTimePart (DOUBLE dbDate)
{
    dbDate = CLIP (dbDate, _VOL_MIN_DATE, _VOL_MAX_DATE);

    SYSTEMTIME st = { 0 };
    if (::VariantTimeToSystemTime (dbDate, &st))
        dbDate = ToDate (2000, 1, 1, (INT_P)(UINT_P)st.wHour, (INT_P)(UINT_P)st.wMinute, (INT_P)(UINT_P)st.wSecond, (INT_P)(UINT_P)st.wMilliseconds, dbDate);

    return dbDate;
}

INT GetSecondsFromMyBaseTime ()
{
    static const FILETIME cs_timeBase = { 0xf3598953, 0x01d2f563 };  // 北京时间 2017/7/5 15:55
    COMPILE_TIME_ASSERT (sizeof (FILETIME) == sizeof (INT64));

    FILETIME timeCurrent = {  0, 0  };
    GetSystemTimeAsFileTime (&timeCurrent);

    const INT64 n64Differ = *(INT64*)&timeCurrent - *(INT64*)&cs_timeBase;
    if (n64Differ < 0)  // 当前时间错误?
        return 0;  // 直接返回0

    const INT nSeconds = (INT)(n64Differ / 10000000i64);  // 将单位从100纳秒转到秒
    return MAX (0, nSeconds);
}

DOUBLE ConvertFileTime (const FILETIME ftConvert)
{
	FILETIME ftLocal;
    SYSTEMTIME st;
    DOUBLE dbDate;

    return ((::FileTimeToLocalFileTime (&ftConvert, &ftLocal) &&
                ::FileTimeToSystemTime (&ftLocal, &st) &&
                ::SystemTimeToVariantTime (&st, &dbDate)) ?
            dbDate : _VOL_MIN_DATE);
}
