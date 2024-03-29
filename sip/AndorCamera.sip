
namespace Andor
{
%TypeHeaderCode
#include <AndorCamera.h>
%End
    enum SpoolingMethod
    {
        SM_SEQ_INT32 = 0,
        SM_ACCUMULATION_DEPENDEND,
        SM_SEQ_INT16,
        SM_MULTI_DIRS,
        SM_RAM,
        SM_16BIT_FITS,
        SM_SIF,
        SM_16BIT_TIFF,
        SM_MULTI_DIRS_COMP
    };

    enum HighCapacityMode
    {
        HC_UNSUPPORTED = -1,
        HIGH_SENSITIVITY = 0,
        HIGH_CAPACITY
    };

    enum GateMode
    {
       FIRE_ANDED_WITH_GATE = 0,
       FIRE_ONLY,
       SMB_GATE_ONLY,
       GATING_ON,
       GATING_OFF,
       DDG
    };

    enum ReadMode
    {
        FULL_VERTICAL_BINNING = 0,
        MULTI_TRACK,
        RANDOM_TRACK,
        SINGLE_TRACK,
        IMAGE
    };

    enum FanMode
    {   FAN_UNSUPPORTED = -1,
        FAN_ON_FULL = 0,
        FAN_ON_LOW,
        FAN_OFF
    };

    enum BaselineClamp
    {
         BLCLAMP_UNSUPPORTED = -1,
	 BLCLAMP_DISABLED = 0,
	 BLCLAMP_ENABLED = 1
    };

  class Camera
  {
%TypeHeaderCode
#include <AndorCamera.h>
%End

  public:

    enum Status {
      Ready, Exposure, Readout, Latency, Fault
    };

    enum ShutterMode{
      FRAME,
      MANUAL
    };


    Camera(const std::string& config_path, int serial_number=0);
    ~Camera();

    void prepareAcq();
    void startAcq();
    void stopAcq();

    void getImageType(ImageType& type /Out/);
    void setImageType(ImageType type);

    void getDetectorType(std::string& type /Out/);
    void getDetectorModel(std::string& model /Out/);
    void getDetectorImageSize(Size& size /Out/);
    HwBufferCtrlObj* getBufferCtrlObj();

    void setTrigMode(TrigMode  mode);
    void getTrigMode(TrigMode& mode /Out/);
	
    void setExpTime(double  exp_time);
    void getExpTime(double& exp_time /Out/);

    void setLatTime(double  lat_time);
    void getLatTime(double& lat_time /Out/);

    void getExposureTimeRange(double& min_expo /Out/, double& max_expo /Out/);
    void getLatTimeRange(double& min_lat /Out/, double& max_lat /Out/);

    void setNbFrames(int  nb_frames);
    void getNbFrames(int& nb_frames /Out/);

    void checkRoi(const Roi& set_roi, Roi& hw_roi /Out/);
    void setRoi(const Roi& set_roi);
    void getRoi(Roi& hw_roi /Out/);

    void checkBin(Bin& /In,Out/);
    void setBin(const Bin&);
    void getBin(Bin& /Out/);

    void setShutterOpenTime(double tm);
    void getShutterOpenTime(double& tm /Out/);
    void setShutterCloseTime(double tm);
    void getShutterCloseTime(double& tm /Out/);
    void setShutter(bool flag);
    void getShutter(bool& flag /Out/);
    void setShutterMode(ShutterMode mode);
    void getShutterMode(ShutterMode& mode /Out/);

    void getPixelSize(double& xsize /Out/, double& ysize /Out/);

    void getStatus(Andor::Camera::Status& status /Out/);

    void initialiseController();
    void initAdcSpeed();
    void setAdcSpeed(int index);
    void getAdcSpeed(int& index /Out/);
    void getAdcSpeedInMhz(float& adc /Out/);
    void getAdcSpeedMaxIndex(int &max_index /Out/);
    void getAdcSpeedPaireString(int index, std::string& paire /Out/);
    void initVsSpeed();
    void setVsSpeed(int vss);
    void getVsSpeed(int& vss /Out/);
    void getVsSpeedMaxIndex(int& max_index /Out/);
    void getVsSpeedString(int index, std::string& speed /Out/);
    void initPGain();
    void setPGain(int gain);
    void getPGainMaxIndex(int& max_index /Out/);
    void getPGainString(int index, std::string& pgain /Out/);

    void getPGain(int& gain /Out/);
    void setFastExtTrigger(bool flag);
    void getFastExtTrigger(bool& flag /Out/);
    void setShutterLevel(int level);
    void getShutterLevel(int& level /Out/);
    void setTemperatureSP(int temp);
    void getTemperatureSP(int& temp);
    void getTemperature(int& temp /Out/);
    void setCooler(bool flag);
    void getCooler(bool& flag /Out/);
    void getCoolingStatus(std::string& status /Out/);
    void setSpooling(bool flag, Andor::SpoolingMethod method, std::string path, int frameBufferSize);
    void setHighCapacity(Andor::HighCapacityMode mode);
    void getHighCapacity(Andor::HighCapacityMode& mode /Out/);
    void setGateMode(Andor::GateMode mode);
    void setFanMode(Andor::FanMode mode);
    void getFanMode(Andor::FanMode& mode /Out/);

    //void setReadMode(Andor::ReadMode mode);
    void setBaselineClamp(Andor::BaselineClamp mode);
    void getBaselineClamp(Andor::BaselineClamp& mode /Out/);
    
  private:
    Camera(const Andor::Camera&);
  };

};
