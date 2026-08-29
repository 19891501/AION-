from .cases import CAS, FAMILLES, couverture

__all__ = ["CAS", "FAMILLES", "couverture"]

# runner (campagne, Rapport, ...) disponible si le module complet est présent
try:
    from .runner import Rapport, campagne, comparer, ecrire

    __all__ += ["Rapport", "campagne", "comparer", "ecrire"]
except ImportError:
    pass
