#pragma once
#include <string>



void AddProxyUserDataList(int browserID, const std::string& url, const std::string& user, const std::string& password);

//取browser的代理
bool GetBrowserProxyUserData(int browserID, const std::string& urlport, std::string& user, std::string& password);

//取全局
bool GetGlobalProxyUserData(const std::string& urlport, std::string& user, std::string& password);

//这里的url地址+端口号，但是没有前缀
bool GetProxyUserData(int browserID, const std::string& urlport, std::string& user, std::string& password);

//通过browserID取出代理地址
std::string GetBrowserProxyUrl(int browserID);

//清理浏览ID对应的动态代理
void ClearProxyUserDataList(int browserID);

//清理全部代理数据
void ClearProxyUserDataList();