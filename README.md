# General SAXS data processing GUI (RAGui)

This GUI is constructed based on silx library developed at ESRF

Notes on starating the GUI using a terminal if already installed in folder RAGui:

    conda activate RAGUI_env
    cd RAGui
    python RAGui.py


For Linux users:

Minimal environment install for linux based operating systems using miniconda 3 with python 3.8:

    step 1: wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    step 2: bash ./Miniconda3-latest-Linux-x86_64.sh
    step 3: conda create -n RAGUI_env python=3.8 pyfai pyqt dask bitshuffle
    step 4: conda activate RAGUI_env
    step 5: python RAGUI_env/RAGui.py   
    

For WINDOWS (10+) users:

To get RAGui running on your windows computer the easiest way is to use the ubuntu version of wsl.
Wsl is a basically a contained linux vitrual OS officially supported by windows.
You will also need an Xviewer, we recommend Xming

    Installing Xming:
        step 1: Google Xming, download and install the Xming X Server for windows
        step 2: Start XLaunch and just press the next button
            NOTE: remember to launch your Xviewer everytime you want to run RAGui
            NOTE: On the fourth pannel (Finish configuration) you can save the configuration so its starts on startup (it is a very light application) 

    Installing WSL Ubuntu:
        step 1: Go to microsoft store and use the searchfunction to search for "ubuntu"
        step 2: Install the "Ubuntu" app

    Installing and starting anaconda with RAGui in Ubuntu:
            NOTE: For each of the steps 1-4 type/copy in the text to the command line in Ubuntu and press enter
                For step 1 you will be prompted to put in you username and password that you set is step 0
                A prompt will appear at one point in step 1, use the arrow keys to change the prompt to yes and press enter
                There will be two progess bars appearing in step 1 so be patient   
            NOTE: For step 3 you will be asked to aprove license terms, type "yes" and press enter. Press enter when prompted to confirm location and when asked to append location to PATH.
                When asked if you want visual studio code type "no" and press enter
            NOTE: The next time you want to start PyQtFAI just do steps 0, 7, 8 and 9

        step 0: Start your Ubuntu, set a username and password
        step 1: sudo bash -c ' apt update -y && apt full-upgrade -y && apt-get install git libxkbcommon-x11-0 -y && export DISPLAY=localhost:0.0' 
        step 2: echo -e "export DISPLAY=localhost:0.0\nexport PATH=\"\$HOME/miniconda3/bin/:\$PATH\"\n$(cat .bashrc)" >.bashrc
        step 3: (if at MAXIV): git clone https://gitlab.maxiv.lu.se/ext-shunyu/general-saxs-data-processing-gui.git
                (if NOT at MAXIV): git clone https://github.com/MaxIV-KitsControls/RAGui.git
                NOTE: for username and pw ask the cosaxs staff
        step 4: wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
        step 5: bash ./Miniconda3-latest-Linux-x86_64.sh
        step 6: (if downloaded from MAXIV): conda env create -f general-saxs-data-processing-gui/RAGui_env.yml
                (if NOT downloaded at MAXIV): conda env create -f RAGui/RAGui_env.yml
        step 7: conda activate RAGui_env
        step 8: (if downloaded from MAXIV): cd general-saxs-data-processing-gui
                (if NOT downloaded at MAXIV): cd RAGui
        step 9: python RAGui.py


        NOTE: when you want to get your data into the analysis: click on "Browser", and you will find your data by clicking on the "Computer" icon, then the "hard drive icon" named "/". The go to mnt/c/Users/"username"/"your usb or external harddrive or werever you have your data" 
