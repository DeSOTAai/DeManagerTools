#!/bin/bash
echo "Upgrading DeManagerTools to version: __version__">> __demanager_log__
echo "Welcome to this fresh upgrade"
echo "   program name   : DeSOTA - Manager Tools"
echo "   program version: __version__"

# QUIET UNISTALL

# Download Program : meanwhile Exe has been closed for project delete (why i don delete first) 
echo
echo "Downloading Program"
wget __download_url__ -O __tmp_compress_file__ &>/dev/nul
echo "Done"

# Create BackUP:
echo
echo "Creating Program BackUP"
cp -r __program_dir__ __backup_dir__ &>/dev/nul
echo "Done"

# Delete Project Folder
echo
echo "Deleting Program Folder"
if [ -d __program_dir__ ]; then
  rm -rf __program_dir__ &>/dev/nul
fi

# Check if folder still exist
if [ -d __program_dir__ ]; then
  rm -rf __program_dir__ &>/dev/nul
  echo "Fail: Delete Program Error"
  echo "     Tip1: Close anything related to this program"
  echo "     Tip2: Delete this folder __program_dir__"
  echo "(Take any of the tips above before continuing)"
  read -n1 -r -p "Press any key to continue..." key && echo
fi
if [ ! -d __program_dir__ ]; then
  echo "Done"
fi

# Uncompress Program
echo
echo "Uncompressing Download"
mkdir -p __program_dir__ &>/dev/nul
apt install libarchive-tools -y &>/dev/nul && bsdtar -xzvf __tmp_compress_file__ -C __program_dir__ --strip-components=1 &>/dev/nul
rm -f __tmp_compress_file__
echo "Done"

# Start Program
echo
echo "Starting Program"
echo "WARNING: DON'T CLOSE ME, PLEASE!"
echo "[ After you close the program I'll close automatically. ]"
chown -R __user__ __program_dir__
echo "3">__launch_flag__
chown -R __user__ __launch_flag__  
while : ; do
  lauch_flag_raw=$(<__launch_flag__)
  lauch_flag=${lauch_flag_raw##*( )}
  if [ $lauch_flag -eq 0 ]; then
    echo "Done"
    echo "Upgrading DeManagerTools v__version__ : SUCESS" >> __demanager_log__
    if [ -d __backup_dir__ ]; then
      rm -rf __backup_dir__  &>/dev/nul
    fi
    if [ -e __launch_flag__ ]; then
      rm -rf __launch_flag__  &>/dev/nul
    fi
    rm -- "__upgrade_path__" & chown -R __user__ __program_dir__ & exit 0
  fi
  if [ $lauch_flag -eq 1 ]; then
    break
  fi
done
echo "Fail"
echo "Upgrading DeManagerTools v__version__ : FAIL" >> __demanager_log__

# Regress to BackUP
echo
echo "Regress to Previous Version"
echo "WARNING: DON'T CLOSE ME, PLEASE!"
echo "[ After you close the program I'll close automatically. ]"
if [ -d __program_dir__ ]; then
  rm -rf __program_dir__ &>/dev/nul
fi
mv __backup_dir__ __program_dir__
chown -R __user__ __program_dir__
echo "2">__launch_flag__
chown -R __user__ __launch_flag__
while : ; do
  lauch_flag_raw=$(<__launch_flag__)
  lauch_flag=${lauch_flag_raw##*( )}
  if [ $lauch_flag -ne 2 ]; then
    break
  fi
done

if [ $lauch_flag -ne 0 ]; then
  echo "Fail: Regress to Previous Version Error"
  echo "  Tip: Re-Start your Computer then run this command"
  echo "       sudo bash __upgrade_path__"
  chown -R __user__ __program_dir__
  if [ -e __launch_flag__ ]; then
    rm -rf __launch_flag__  &>/dev/nul
  fi
  exit 1
fi
if [ ! -d __backup_dir__ ]; then
  rm -rf __backup_dir__  &>/dev/nul
fi
if [ -e __launch_flag__ ]; then
  rm -rf __launch_flag__  &>/dev/nul
fi
chown -R __user__ __program_dir__
exit 0
