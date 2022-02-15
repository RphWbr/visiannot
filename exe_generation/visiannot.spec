# -*- mode: python -*-

block_cipher = None

pkg_dir = '..'

datas_list = [
    ('%s/visiannot/visiannot/components/Images/*.jpg' % pkg_dir, 'Images')
]

a = Analysis(['%s/visiannot/__main__.py' % pkg_dir],
             binaries=[],
             datas=datas_list,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ViSiAnnoT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True)
