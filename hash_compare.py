#!/usr/bin/env python3
"""
Script de comparaison de fichiers par hash entre deux dossiers.
Affiche les résultats dans le terminal et exporte vers Excel.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime
import argparse

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich import box
except ImportError:
    print("Erreur: rich n'est pas installé. Installez-le avec: pip install rich")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("Erreur: pandas n'est pas installé. Installez-le avec: pip install pandas openpyxl")
    sys.exit(1)


class HashComparator:
    """Classe pour comparer les fichiers de deux dossiers par leur hash."""
    
    def __init__(self, directory1: Path, directory2: Path, algorithm: str = 'sha256'):
        """
        Initialise le comparateur.
        
        Args:
            directory1: Premier dossier à comparer
            directory2: Deuxième dossier à comparer
            algorithm: Algorithme de hash à utiliser (md5, sha1, sha256)
        """
        self.directory1 = Path(directory1)
        self.directory2 = Path(directory2)
        self.algorithm = algorithm
        self.console = Console()
        
        # Vérifier que les dossiers existent
        if not self.directory1.exists():
            raise FileNotFoundError(f"Le dossier '{self.directory1}' n'existe pas.")
        if not self.directory2.exists():
            raise FileNotFoundError(f"Le dossier '{self.directory2}' n'existe pas.")
        
        if not self.directory1.is_dir():
            raise NotADirectoryError(f"'{self.directory1}' n'est pas un dossier.")
        if not self.directory2.is_dir():
            raise NotADirectoryError(f"'{self.directory2}' n'est pas un dossier.")
    
    def calculate_hash(self, file_path: Path) -> str:
        """
        Calcule le hash d'un fichier.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Hash hexadécimal du fichier
        """
        hash_obj = hashlib.new(self.algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                # Lire le fichier par chunks pour gérer les gros fichiers
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except (IOError, OSError) as e:
            self.console.print(f"[red]Erreur lors de la lecture de {file_path}: {e}[/red]")
            return ""
    
    def scan_directory(self, directory: Path, progress: Progress = None) -> Dict[str, List[Path]]:
        """
        Scanne un dossier et calcule les hash de tous les fichiers.
        
        Args:
            directory: Dossier à scanner
            progress: Objet Progress de rich pour afficher la progression
            
        Returns:
            Dictionnaire {hash: [liste des fichiers avec ce hash]}
        """
        hash_to_files: Dict[str, List[Path]] = {}
        files = list(directory.rglob('*'))
        files = [f for f in files if f.is_file()]
        
        task = None
        if progress:
            task = progress.add_task(f"[cyan]Scan de {directory.name}...", total=len(files))
        
        for file_path in files:
            if progress and task is not None:
                progress.update(task, advance=1, description=f"[cyan]Traitement de {file_path.name}...")
            
            file_hash = self.calculate_hash(file_path)
            if file_hash:
                relative_path = file_path.relative_to(directory)
                if file_hash not in hash_to_files:
                    hash_to_files[file_hash] = []
                hash_to_files[file_hash].append(relative_path)
        
        return hash_to_files
    
    def compare(self) -> Dict:
        """
        Compare les deux dossiers et retourne les résultats.
        
        Returns:
            Dictionnaire contenant les résultats de la comparaison
        """
        self.console.print(f"\n[bold blue]Comparaison des dossiers:[/bold blue]")
        self.console.print(f"  Dossier 1: [green]{self.directory1}[/green]")
        self.console.print(f"  Dossier 2: [green]{self.directory2}[/green]")
        self.console.print(f"  Algorithme: [yellow]{self.algorithm.upper()}[/yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            hash_dict1 = self.scan_directory(self.directory1, progress)
            hash_dict2 = self.scan_directory(self.directory2, progress)
        
        # Analyser les résultats
        hashes1 = set(hash_dict1.keys())
        hashes2 = set(hash_dict2.keys())
        
        common_hashes = hashes1 & hashes2
        only_in_dir1 = hashes1 - hashes2
        only_in_dir2 = hashes2 - hashes1
        
        # Construire les listes de fichiers
        files_only_in_dir1 = []
        files_only_in_dir2 = []
        files_in_both = []
        
        for hash_val in only_in_dir1:
            for file_path in hash_dict1[hash_val]:
                files_only_in_dir1.append({
                    'hash': hash_val,
                    'fichier': str(file_path),
                    'dossier': self.directory1.name
                })
        
        for hash_val in only_in_dir2:
            for file_path in hash_dict2[hash_val]:
                files_only_in_dir2.append({
                    'hash': hash_val,
                    'fichier': str(file_path),
                    'dossier': self.directory2.name
                })
        
        for hash_val in common_hashes:
            for file_path1 in hash_dict1[hash_val]:
                for file_path2 in hash_dict2[hash_val]:
                    files_in_both.append({
                        'hash': hash_val,
                        'fichier_dossier1': str(file_path1),
                        'fichier_dossier2': str(file_path2),
                        'dossier1': self.directory1.name,
                        'dossier2': self.directory2.name
                    })
        
        return {
            'files_only_in_dir1': files_only_in_dir1,
            'files_only_in_dir2': files_only_in_dir2,
            'files_in_both': files_in_both,
            'stats': {
                'total_files_dir1': sum(len(files) for files in hash_dict1.values()),
                'total_files_dir2': sum(len(files) for files in hash_dict2.values()),
                'unique_hashes_dir1': len(hash_dict1),
                'unique_hashes_dir2': len(hash_dict2),
                'common_hashes': len(common_hashes),
                'only_in_dir1': len(only_in_dir1),
                'only_in_dir2': len(only_in_dir2),
                'files_in_both_count': len(files_in_both)
            }
        }
    
    def display_results(self, results: Dict):
        """
        Affiche les résultats dans le terminal avec un formatage visuel.
        
        Args:
            results: Résultats de la comparaison
        """
        stats = results['stats']
        
        # Panel de statistiques
        stats_text = f"""
[bold]Fichiers dans le dossier 1:[/bold] {stats['total_files_dir1']}
[bold]Fichiers dans le dossier 2:[/bold] {stats['total_files_dir2']}
[bold]Hash uniques dans le dossier 1:[/bold] {stats['unique_hashes_dir1']}
[bold]Hash uniques dans le dossier 2:[/bold] {stats['unique_hashes_dir2']}
[bold]Hash communs:[/bold] {stats['common_hashes']}
[bold]Fichiers identiques:[/bold] {stats['files_in_both_count']}
[bold]Fichiers uniquement dans le dossier 1:[/bold] {len(results['files_only_in_dir1'])}
[bold]Fichiers uniquement dans le dossier 2:[/bold] {len(results['files_only_in_dir2'])}
        """
        
        self.console.print(Panel(stats_text, title="[bold cyan]Statistiques[/bold cyan]", border_style="cyan"))
        
        # Tableau des fichiers identiques
        if results['files_in_both']:
            table = Table(title="[bold green]Fichiers Identiques (même hash)[/bold green]", box=box.ROUNDED)
            table.add_column("Hash", style="cyan", no_wrap=False)
            table.add_column(f"Fichier dans {self.directory1.name}", style="green")
            table.add_column(f"Fichier dans {self.directory2.name}", style="green")
            
            for item in results['files_in_both'][:50]:  # Limiter à 50 pour l'affichage
                table.add_row(
                    item['hash'][:16] + "...",
                    item['fichier_dossier1'],
                    item['fichier_dossier2']
                )
            
            if len(results['files_in_both']) > 50:
                table.add_row("...", f"[dim]({len(results['files_in_both']) - 50} autres fichiers)[/dim]", "")
            
            self.console.print(table)
        
        # Fichiers uniquement dans le dossier 1
        if results['files_only_in_dir1']:
            table = Table(title=f"[bold yellow]Fichiers Uniquement dans {self.directory1.name}[/bold yellow]", box=box.ROUNDED)
            table.add_column("Hash", style="cyan", no_wrap=False)
            table.add_column("Fichier", style="yellow")
            
            for item in results['files_only_in_dir1'][:50]:
                table.add_row(
                    item['hash'][:16] + "...",
                    item['fichier']
                )
            
            if len(results['files_only_in_dir1']) > 50:
                table.add_row("...", f"[dim]({len(results['files_only_in_dir1']) - 50} autres fichiers)[/dim]")
            
            self.console.print(table)
        
        # Fichiers uniquement dans le dossier 2
        if results['files_only_in_dir2']:
            table = Table(title=f"[bold yellow]Fichiers Uniquement dans {self.directory2.name}[/bold yellow]", box=box.ROUNDED)
            table.add_column("Hash", style="cyan", no_wrap=False)
            table.add_column("Fichier", style="yellow")
            
            for item in results['files_only_in_dir2'][:50]:
                table.add_row(
                    item['hash'][:16] + "...",
                    item['fichier']
                )
            
            if len(results['files_only_in_dir2']) > 50:
                table.add_row("...", f"[dim]({len(results['files_only_in_dir2']) - 50} autres fichiers)[/dim]")
            
            self.console.print(table)
    
    def export_to_excel(self, results: Dict, output_file: str = None):
        """
        Exporte les résultats vers un fichier Excel.
        
        Args:
            results: Résultats de la comparaison
            output_file: Nom du fichier de sortie (optionnel)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comparaison_hash_{timestamp}.xlsx"
        
        output_path = Path(output_file)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Feuille 1: Statistiques
            stats_df = pd.DataFrame([results['stats']])
            stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
            
            # Feuille 2: Fichiers identiques
            if results['files_in_both']:
                df_both = pd.DataFrame(results['files_in_both'])
                df_both.to_excel(writer, sheet_name='Fichiers Identiques', index=False)
            
            # Feuille 3: Fichiers uniquement dans le dossier 1
            if results['files_only_in_dir1']:
                df_dir1 = pd.DataFrame(results['files_only_in_dir1'])
                df_dir1.to_excel(writer, sheet_name=f'Uniquement {self.directory1.name}', index=False)
            
            # Feuille 4: Fichiers uniquement dans le dossier 2
            if results['files_only_in_dir2']:
                df_dir2 = pd.DataFrame(results['files_only_in_dir2'])
                df_dir2.to_excel(writer, sheet_name=f'Uniquement {self.directory2.name}', index=False)
        
        self.console.print(f"\n[bold green]✓[/bold green] Résultats exportés vers: [cyan]{output_path.absolute()}[/cyan]")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description='Compare les fichiers de deux dossiers en utilisant leurs hash.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python hash_compare.py /chemin/dossier1 /chemin/dossier2
  python hash_compare.py /chemin/dossier1 /chemin/dossier2 --algorithm md5
  python hash_compare.py /chemin/dossier1 /chemin/dossier2 --output resultat.xlsx
        """
    )
    
    parser.add_argument('directory1', type=str, help='Premier dossier à comparer')
    parser.add_argument('directory2', type=str, help='Deuxième dossier à comparer')
    parser.add_argument(
        '--algorithm', '-a',
        choices=['md5', 'sha1', 'sha256'],
        default='sha256',
        help='Algorithme de hash à utiliser (défaut: sha256)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Nom du fichier Excel de sortie (défaut: comparaison_hash_YYYYMMDD_HHMMSS.xlsx)'
    )
    
    args = parser.parse_args()
    
    try:
        comparator = HashComparator(
            Path(args.directory1),
            Path(args.directory2),
            algorithm=args.algorithm
        )
        
        results = comparator.compare()
        comparator.display_results(results)
        comparator.export_to_excel(results, args.output)
        
    except (FileNotFoundError, NotADirectoryError) as e:
        console = Console()
        console.print(f"[bold red]Erreur:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Interruption par l'utilisateur[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Erreur inattendue:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == '__main__':
    main()

