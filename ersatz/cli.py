#!/usr/bin/env python
import click

def cfg2dict(filename):
    filename = os.path.expanduser(os.path.expandvars(filename))
    from ConfigParser import SafeConfigParser
    cfg = SafeConfigParser()
    cfg.read(filename)
    ret = dict()
    for secname in cfg.sections():
        secdict = dict()
        for k,v in cfg.get_items(secname):
            secdict[k] = v
        ret[secname] = secdict
    return ret


@click.group()
@click.option('-c', '--config', 
              help = 'Set configuration file.')
@click.pass_context
def cli(ctx, config):
    ctx.obj['cfg'] = cfg2dict(config)
    return

def main():
    cli(obj=dict())

if '__main__' == __name__:
    main()
