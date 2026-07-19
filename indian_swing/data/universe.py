from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.core.symbols import SymbolManager
from indian_swing.database.repositories.stock_repo import StockRepository

logger = get_logger(__name__)


class UniverseLoader:
    EXCLUDED_SYMBOLS = {
        "3BBLACKBIO", "AARNAV", "AARTISURF", "AASTHA", "ABANSENT", "ABLBL", "ABMKNO", "ACSTECH",
        "ADVAIT", "ADVANCE", "ADVENTHTL", "AEPL", "AEQUS", "AGL", "AHCL", "AHLWEST", "AKCAPIT",
        "ALGOQUANT", "ALLTIME", "AMAGI", "AMANTA", "AMBALALSA", "AMIRCHAND", "ANTHEM", "ARFIN",
        "ARIHANT", "ARIS", "ARSSBL", "ASHIKA", "ASTAR", "ATLANTAELE", "AYE", "BAJAJST", "BATLIBOI",
        "BCPL", "BEEKAY", "BELLACASA", "BENGALASM", "BHARATCOAL", "BI", "BIMETAL", "BIRLAPREC",
        "BLACKROSE", "BLIL", "BLUESTONE", "BMWVENTLTD", "BNAGROCHEM", "BNALTD", "BONLON",
        "BRIGHOTEL", "BTTL", "BUILDPRO", "CANHLIFE", "CAPILLARY", "CEINSYS", "CHEMBONDCH",
        "CHOLAFIN", "CLEANMAX", "CMPDI", "CMRGREEN", "COCKERILL", "COMFINTE", "CORDELIA",
        "CORONA", "CPEDU", "CPPLUS", "CRAMC", "CRIZAC", "CSM", "DAICHI", "DCMSIL", "DECNGOLD",
        "DEVX", "DISAQ", "DRAGARWQ", "DSFCL", "EASTSILK", "EBGNG", "EFCIL", "ELANTAS", "ELCIDIN",
        "ELITECON", "ELLEN", "ELPROINTL", "EMMVEE", "EMPOWER", "ENRIN", "EPACKPEB", "EUROPRATIK",
        "EXCELSOFT", "FABTECH", "FEDDERSHOL", "FERMENTA", "FINKURVE", "FISCHER", "FRACTAL",
        "FRONTSP", "GANESHCP", "GAUDIUMIVF", "GCSL", "GEMAROMA", "GKENERGY", "GKSL", "GLOBECIVIL",
        "GLOTTIS", "GNRL", "GOODYEAR", "GRADIENTE", "GRANDOAK", "GRAUWEIL", "GRAVISSHO", "GROWW",
        "GSPCROP", "GYFTR", "HALDER", "HALDYNGL", "HAWKINCOOK", "HBESD", "HDBFS", "HEXAGON",
        "HILINFRA", "ICICIAMC", "IGCL", "INA", "INDIQUBE", "INDPRUD", "INNOVISION", "INVPRECQ",
        "IVALUE", "IWP", "JAINREC", "JARO", "JAYKAY", "JKIPL", "JSWCEMENT", "KALPATARU", "KALYANI",
        "KAMAHOLD", "KANCHI", "KENNAMET", "KIRANVYPAR", "KIRLFER", "KISSHT", "KLBRENG-B",
        "KNACK", "KOTIC", "KOVAI", "KPL", "KSHINTL", "KSR", "KUSUMGAR", "KWIL", "LAHOTIOV",
        "LASERPOWER", "LAXMIINDIA", "LENSKART", "LGEINDIA", "LOTUSDEV", "MADHAVIPL", "MAFATIND",
        "MAJESAUT", "MARKOLINES", "MARSONS", "MBEL", "MCCHRLS-B", "MEESHO", "MEIL", "MENNPIS",
        "MERCANTILE", "MERCURYEV", "METROGLOBL", "MIDWESTLTD", "MMWL", "MODINATUR", "MODIS",
        "MONEYBOXX", "NATIONSTD", "NEAGI", "NEPHROPLUS", "NEUEON", "NILE", "NIMBSPROJ", "NIRLON",
        "NITTAGELA", "NOVARTIND", "OMFREIGHT", "OMNI", "OMPOWER", "ORKLAINDIA", "OSWALPUMPS",
        "PACEDIGITK", "PARKHOSPS", "PATELRMART", "PAUSHAKLTD", "PICCADIL", "PINELABS", "PIONRINV",
        "PIRAMALFIN", "PML", "PNGSREVA", "POWERICA", "PRADPME", "PRAVEG", "PREMCO", "PWL",
        "QUINT", "RAJPALAYAM", "RAMBHAJO", "RAYMONDREL", "REGAAL", "RHETAN", "RIR", "RMC",
        "RNBDENIMS", "RRIL", "RSDFIN", "RSL", "RUBICON", "RUDRA", "SAATVIKGL", "SAHLIBHFI",
        "SAIPARENT", "SAMBHV", "SAPPL", "SAYAJIHOTL", "SCANSTL", "SEDEMAC", "SEIL", "SGFIN",
        "SGMART", "SHADOWFAX", "SHANTIGOLD", "SHARDUL", "SHBAJRG", "SHILCTECH", "SHINDL",
        "SHIVAUM", "SHREEJISPG", "SHRIKRISH", "SHRINGARMS", "SICAGEN", "SIKA", "SINGERIND",
        "SKFINDUS", "SMARTWORKS", "SOLARWORLD", "SONAL", "SRTL", "STLNETWORK", "STUDDS",
        "STYL", "SUDEEPPHRM", "SUMEETINDS", "SURYALA", "SYSTMTXC", "TAALTECH", "TAMBOLIIN",
        "TATACAP", "TCC", "TECHNVISN", "TENNIND", "THACKER", "THAKDEV", "TIGERLOGS", "TIMEX",
        "TMCV", "TRANSPEK", "TRAVELFOOD", "TRUALT", "TURTLEMINT", "ULTRAMAR", "URBANCO",
        "UTLSOLAR", "VAML", "VEDPOWER", "VELJAN", "VERTOZ", "VIDYAWIRES", "VIKRAMSOLR",
        "VIKRAN", "VISL", "VIVIMEDLAB", "VMSTMT", "VOEPL", "VOGL", "WAAREEINDO", "WAKEFIT",
        "WELSPLSOL", "WEWORK", "WPIL", "ZFSTEERING", "ZSARACOM"
    }

    def __init__(self, session: Session, csv_path: str | Path | None = None) -> None:
        self.session = session
        self.csv_path = Path(csv_path or settings.universe_file)

    def load_universe(self) -> int:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Universe file {self.csv_path} not found")

        records: list[dict] = []
        with self.csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for raw_row in reader:
                # EQUITY_L.csv has leading spaces in column names — strip them all
                row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in raw_row.items()}
                raw_symbol = row.get("Symbol") or row.get("SYMBOL") or ""
                if not raw_symbol:
                    continue
                try:
                    symbol = SymbolManager.normalize_internal_symbol(raw_symbol)
                except ValueError:
                    continue
                records.append(
                    {
                        "exchange": "NSE",
                        "symbol": symbol,
                        # EQUITY_L.csv uses "ISIN NUMBER"; nifty lists use "ISIN Code"
                        "isin": (
                            row.get("ISIN NUMBER")
                            or row.get("Isin") 
                            or row.get("ISIN") 
                            or row.get("ISIN Code")
                            or row.get("ISIN CODE")
                            or None
                        ),
                        # EQUITY_L.csv uses "NAME OF COMPANY"; nifty lists use "Company Name"
                        "name": (
                            row.get("NAME OF COMPANY")
                            or row.get("Company Name")
                            or row.get("COMPANY NAME")
                            or symbol
                        ),
                        "sector": row.get("Industry") or row.get("INDUSTRY") or None,
                        "industry": row.get("Industry") or row.get("INDUSTRY") or None,
                        "instrument_type": "EQUITY",
                        "is_active": symbol not in self.EXCLUDED_SYMBOLS,
                    }
                )

        repo = StockRepository(self.session)
        count = repo.bulk_upsert(records)
        self._ensure_benchmark(repo)
        logger.info("universe.loaded", count=count, file=str(self.csv_path))
        return count

    def _ensure_benchmark(self, repo: StockRepository) -> None:
        repo.upsert(
            symbol=settings.scanner.benchmark_symbol,
            exchange=settings.scanner.benchmark_exchange,
            name="NIFTY 50",
            instrument_type="INDEX",
            is_active=True,
        )
