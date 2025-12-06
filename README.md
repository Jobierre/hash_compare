# Hash Compare

Script Python pour comparer les fichiers de deux dossiers en utilisant leurs hash (MD5, SHA1, SHA256).

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python hash_compare.py /chemin/dossier1 /chemin/dossier2
```

### Options

- `--algorithm` ou `-a` : Algorithme de hash (`md5`, `sha1`, `sha256`). Par défaut: `sha256`
- `--output` ou `-o` : Nom du fichier Excel de sortie. Par défaut: `comparaison_hash_YYYYMMDD_HHMMSS.xlsx`

### Exemples

```bash
# Comparaison basique
python hash_compare.py ./dossier1 ./dossier2

# Avec MD5
python hash_compare.py ./dossier1 ./dossier2 --algorithm md5

# Avec nom de fichier personnalisé
python hash_compare.py ./dossier1 ./dossier2 --output resultat.xlsx
```

## Sortie

- **Terminal** : Affichage visuel avec statistiques et tableaux colorés
- **Excel** : Fichier avec 4 feuilles :
  - Statistiques
  - Fichiers identiques
  - Fichiers uniquement dans le dossier 1
  - Fichiers uniquement dans le dossier 2

