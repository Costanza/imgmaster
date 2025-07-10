import click


@click.group()
def cli():
    """Image Master - A powerful image processing CLI tool."""
    pass


@cli.command()
def build():
    """Build command - placeholder for future functionality."""
    click.echo("Build command executed!")


if __name__ == "__main__":
    cli()
