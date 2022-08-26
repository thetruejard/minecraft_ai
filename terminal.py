
from distutils.command.build import build
from email import header
import os
import time

from rich.columns import Columns
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.tree import Tree

from minecraftai import MinecraftAI


console = None


def build_tree(model: MinecraftAI):
    model_tree = Tree(model.name, style='bright_cyan', guide_style='blue')
    conn_head_tree = model_tree.add('Connections', style='cyan', guide_style='magenta')
    conns_table = Table(*[c.name for c in model.connections.values()], style='bright_black', header_style='bright_magenta')
    conns_table.add_row(*[f'[white]{c.queue.qsize()}[/white] / {c.queue.maxsize}' \
        for c in model.connections.values()], style='bright_black')
    conn_head_tree.add(conns_table)
    proc_head_tree = model_tree.add('Processes', style='cyan', guide_style='magenta')
    for proc in model.processes.values():
        proc_tree = proc_head_tree.add(proc.name, style='bright_magenta', guide_style='green')
        props = proc.get_properties()
        if len(props) > 0:
            prop_table = Table(*props.keys(), style='bright_black', header_style='bright_green')
            prop_table.add_row(*[str(p) for p in props.values()], style='white')
            proc_tree.add(prop_table, guide_style='magenta')
        #for i in proc.input_connections:
        #    proc_tree.add(str(i), style='bright_magenta', guide_style='magenta')
    return model_tree


def during_run(model: MinecraftAI):
    global console
    console = Console()

    console.rule('[cyan]Minecraft AI[/cyan]', style='red')
    console.print('something something')
    console.rule(style='red')

    try:

        with Live(build_tree(model), console=console) as live:
            while True:
                time.sleep(0.5)
                live.update(build_tree(model))

    except KeyboardInterrupt:
        pass

    console = None
