import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helper import download_data
from data.Index import nifty_next_500_symbols
import pandas as pd
import time

def analyze_failures():
    """Analyze why symbols are failing to download"""
    
    # Failed symbols from the test results
    failed_symbols = [
        'BALAJIPHOS.NS', 'ABHIINT.NS', 'CPSSHAPER.NS', 'SHANTIOVERS.NS', 'LLOYDSLUX.BO',
        'ASHIMA.BO', 'SHEETALUNI.BO', 'VASULOG.BO', 'ELINEL.BO', 'HITACHIEN.NS',
        'ECOSMOB.BO', 'SARLAPERF.BO', 'AUTHUM.BO', 'RMDRIP.BO', 'SILGO.BO',
        'SAHPOLY.BO', 'COUNTRYCON.BO', 'BASILIC.BO', 'URAVI.BO', 'PANSARI.BO',
        'CARYSL.BO', 'BOHRIND.BO', 'HOACFOODS.BO', 'DANISHPOW.BO', 'ALPEX.BO',
        'SUNDARMHLD.BO', 'SHANKARABUILD.BO', 'KARNIKA.BO', 'MYMUDRA.BO', 'ASPIRE.BO',
        'MODIRUBBE.BO', 'ORIENTAROM.BO', 'WAAREENG.BO', 'GANINFRA.BO', 'INFINPHARMA.BO',
        'ABDIST.BO', 'NAHARPOLYF.BO', 'MASTERTRUST.BO', 'FOSECO.BO', 'MOREPENLABS.BO',
        'AGARTOUG.BO', 'GPECO.BO', 'SWARAJSUIT.BO', 'BODAL.BO', 'VINYAS.BO',
        'MAXVOLT.BO', 'ROSSELLTECH.BO', 'GRILL.BO', 'SOLEXENERGY.BO', 'INDPEST.BO',
        'TANKUP.BO', 'VASCON.BO', 'PRIZOR.BO', 'DCX.BO', 'MAHICKRA.BO',
        'ROTOPUMP.BO', 'ARUNAYA.BO', 'RANEMA.BO', 'STANDARDGL.BO', 'UNIHEALTH.BO',
        'KHAITAN.BO', 'GROBTEA.BO', 'VSSSL.BO', 'DIENSTEN.BO', 'MASONINFRA.BO',
        'AARTISRF.BO', 'AARON.BO', 'VISIONINFRA.BO', 'VISAKA.NS', 'MASTER.BO',
        'VAIDAA.BO', 'BLSINFO.BO', 'DOCMODE.BO', 'PRECOT.BO', 'TECHNO.BO',
        'VINSYS.BO', 'SUPREMEPET.BO', 'DLINK.BO', 'RRW.BO', 'ABANS.BO',
        'TRANSTEEL.BO', 'BANNARI.BO', 'VILASTRANS.BO', 'UNICOMMERCE.BO', 'AUSOM.BO',
        'KRITINDT.BO', 'LFIC.BO', 'ANLONTECH.BO', 'SEJAL.BO', 'KRITIND.BO',
        'BHARATSEATS.BO', 'EUREKAFORBE.BO', 'PENLAND.BO', 'HPLELEC.BO', 'ABD.BO',
        'SPAPP.BO', 'SONU.BO', 'MTAR.NS', 'NGLFINECHEM.BO', 'SABEVENT.BO',
        'VADIVARHE.BO', 'ORIANA.BO', 'BURGERKING.NS', 'THINKHATE.BO', 'JBMATO.BO',
        'GODAVARIBUS.BO', 'SYLVAN.BO', 'PIX.BO', 'COMMITTED.BO', 'ELEGANZ.BO',
        'MROTEK.BO', 'SDRETAIL.BO', 'KALPATPOWR.BO', 'VISHMEGA.BO', 'READYMIX.BO',
        'SETUBANDHAN.BO', 'FIDEL.BO', 'BAJELPROJ.BO', 'MADHUMASALA.BO', 'DVDGVIJAY.BO',
        'DHARICORP.BO', 'HECINFRA.BO', 'SBCEXPORT.BO', 'JAKHARIA.BO', 'PHOENIXOVS.BO',
        'GSMFOILS.BO', 'SIGMASOLVE.BO', 'ZOTA.BO', 'JUBLAGRI.BO', 'OSELDEVICES.BO',
        'MAHAMAYA.BO', 'GAJANANN.BO', 'APS.BO', 'SPREF.BO', 'GRP.BO',
        'ANYAFERTIL.BO', 'GANESHBHRT.BO', 'VELSINTL.BO', 'FOCE.BO', 'AARTIPHARMA.BO',
        'TECHERA.BO', 'PHANTOMFX.BO', 'IBL.BO', 'GKW.BO', 'ROLLATAINERS.BO',
        'SIXSIGMA.BO', 'DIVGI.NS', 'BANKRAINTREE.BO', 'JMA.BO', 'TII.BO',
        'VIPCIND.BO', 'EUROFRESH.BO', 'IPHOSPLT.BO', 'INDIANIPPON.BO', 'GLOBEINTL.BO',
        'HINDWARE.NS', 'SUPREMEPOW.BO', 'INNOMET.BO', 'CIGNITITECH.BO', 'AATMAJ.BO',
        'TECHNOCRAFT.BO', 'AVITEX.BO', 'TRANSRAIL.BO', 'MOSUTILITIES.BO', 'PATTECH.BO',
        'CADSYS.BO', 'VISAGLOBAL.BO', 'ROBUSTHOT.BO', 'ONLIFECAP.BO', 'AGIINFRA.BO',
        'GLOBALEDU.BO', 'ANTONY.BO', 'AMBANIORG.BO', 'EXWIRES.BO', 'PRAMARA.BO',
        'KAPSTON.BO', 'ALLETHECH.BO', 'HOLMARC.BO', 'RAJCASS.BO', 'ATLAA.BO',
        'ZINKA.BO', 'ISHANDYES.BO', 'KAYCEEEN.BO', 'ASINGRAN.BO', 'KOTHARISUG.BO',
        'MAANLUM.BO', 'MAHALAXFABR.BO', 'SHUBHSBIOE.BO', 'ORICON.BO', 'MAXEST.BO',
        'NAMOEWASTE.BO', 'JAYSHREETEA.BO', 'BLACKBOX.BO', 'AVRO.BO', 'AVTIL.BO',
        'GMMPFAUDLER.BO', 'ABRETS.BO', 'PARAGON.BO', 'FUSIONRS5.BO', 'KNAGRI.BO',
        'PRABHAEN.BO', 'SINTERCOM.BO', 'MADHYAPR.BO', 'INDEMULSIF.BO', 'JIWANRAM.BO',
        'MASKIN.BO', 'LEMERITE.BO', 'SONABLW.BO', 'SHIGAN.BO', 'QVCEXPORTS.BO',
        'GOCLENG.BO', 'MMPIL.BO', 'TIRUFORG.BO', 'DHUNSRITEA.BO', 'IDEALTPT.BO',
        'PETROCARB.BO', 'IFBAGROIND.BO', 'HYUNDAIMOTR.NS', 'ELECTFORC.BO', 'ASPINWALL.BO',
        'RDS.BO', 'MADHYABHA.BO', 'AIONTECHSO.BO', 'LAXMICOT.BO', 'WESCARR.BO',
        'ESPIRITSTON.BO', 'POPULARV.BO', 'SIGNORIA.BO', 'ADITULTRA.BO', 'SATKARTAR.BO',
        'HEXAWARE.NS', 'SUNDARMPON.BO', 'GACMTECH.BO', 'DUDIGITL.BO', 'INNOVANATH.BO',
        'NAMANINS.BO', 'ACCORDSYN.BO', 'SUNLITEREC.BO', 'SHRADHAINFR.BO', 'ABSMARINE.BO',
        'RJLLTD.BO', 'JAICORP.BO', 'WSINDUSTRI.BO', 'SCLAYTON.BO', 'USHAFIN.BO',
        'BEARDSELL.BO', 'HRHNXTSRVC.BO', 'DIGIKORE.BO', 'MEGA.BO', 'SAJHOTELS.BO',
        'NAGREEKA.BO', 'EXPLEO.BO', 'SASTECH.BO', 'SAHAJFASH.BO', 'ARHAMTECH.BO',
        'TRANSWARR.BO', 'LPSSEC.BO', 'PEARLGLOBAL.BO', 'PARAMDYE.BO', 'PLADA.BO',
        'CUBEX.BO', 'LAXMIGOLDRN.BO', 'PRITISNC.BO', 'DIGICONTENT.BO', 'SHANTHALA.BO',
        'AGUNIV.BO', 'BAWEJASTU.BO', 'AKIIND.BO', 'ANIINT.BO', 'AVPINFRA.BO',
        'SURANISTL.BO', 'ADDICTIVE.BO', 'NEWJAISA.BO', 'TBICORN.BO', 'TBO.BO',
        'AMBEYLAB.BO', 'MANAV.BO', 'TEMBO.BO', 'CAMTECH.BO', 'ROXHITECH.BO'
    ]
    
    print(f"Total failed symbols: {len(failed_symbols)}")
    
    # Categorize by exchange
    nse_symbols = [s for s in failed_symbols if s.endswith('.NS')]
    bse_symbols = [s for s in failed_symbols if s.endswith('.BO')]
    
    print(f"\nBy Exchange:")
    print(f"NSE symbols (.NS): {len(nse_symbols)}")
    print(f"BSE symbols (.BO): {len(bse_symbols)}")
    
    # Test a few specific symbols to understand the error patterns
    print(f"\n=== Testing Specific Failed Symbols ===")
    
    test_symbols = [
        'BALAJIPHOS.NS',  # NSE symbol
        'LLOYDSLUX.BO',   # BSE symbol  
        'HITACHIEN.NS',   # NSE symbol
        'VISAKA.NS',      # NSE symbol
        'MTAR.NS',        # NSE symbol
        'DIVGI.NS',       # NSE symbol
        'HINDWARE.NS',    # NSE symbol
        'BURGERKING.NS',  # NSE symbol
        'HYUNDAIMOTR.NS', # NSE symbol
        'HEXAWARE.NS'     # NSE symbol
    ]
    
    for symbol in test_symbols:
        try:
            print(f"\nTesting: {symbol}")
            data = download_data(symbol, interval='1mo', period='1y')
            if data is not None and len(data) > 0:
                print(f"✓ {symbol} - SUCCESS (got {len(data)} rows)")
            else:
                print(f"✗ {symbol} - NO DATA")
        except Exception as e:
            print(f"✗ {symbol} - Error: {str(e)}")
        
        time.sleep(1)  # Rate limiting
    
    # Check if some symbols might work with different periods
    print(f"\n=== Testing with Different Periods ===")
    
    test_periods = ['1mo', '3mo', '6mo', '1y', '2y']
    test_symbol = 'BALAJIPHOS.NS'
    
    for period in test_periods:
        try:
            print(f"Testing {test_symbol} with period={period}")
            data = download_data(test_symbol, interval='1mo', period=period)
            if data is not None and len(data) > 0:
                print(f"✓ SUCCESS with period={period} (got {len(data)} rows)")
                break
            else:
                print(f"✗ NO DATA with period={period}")
        except Exception as e:
            print(f"✗ ERROR with period={period}: {str(e)}")
        
        time.sleep(1)

if __name__ == "__main__":
    analyze_failures() 