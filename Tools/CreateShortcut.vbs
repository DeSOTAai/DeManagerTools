Set oWS = WScript.CreateObject("WScript.Shell") 
sLinkFile = "%HOMEDRIVE%%HOMEPATH%\Desktop\Desota - Manager Tools.lnk" 
Set oLink = oWS.CreateShortcut(sLinkFile) 
oLink.TargetPath = "%HOMEDRIVE%%HOMEPATH%\Desota\DeManagerTools\dist\Desota - Manager Tools\Desota - Manager Tools.exe" 
oLink.Save 
