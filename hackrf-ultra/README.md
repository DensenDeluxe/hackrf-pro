# HackRF Ultra

HackRF Ultra ist ein eigenständiger Entwurf. Er übernimmt die Konsequenzen aus der Analyse von HackRF Pro (Codename Praline, Revision 1.2.1 in diesem Repository) und ersetzt die Bausteine, an denen diese Architektur physikalisch endet.

Stand **0.1.0-arch**. Das ist ein Schaltplan mit Netzvertrag, Stückliste, Stackup und einem Platinenrahmen. Es ist kein Fertigungspaket: keine BGA-Lands, keine Kupferflächen, keine Gerber. Auf der Platine steht das auch im Siebdruck.

| | HackRF Pro r1.2.1 | HackRF Ultra 0.1 |
|---|---|---|
| Frequenz | 100 kHz bis 6 GHz, Abstimmung bis etwa 7,1 GHz | 9 kHz bis 18 GHz, direkt abgetastet |
| Wandler | MAX5865, 8 Bit, 40 MSPS | AD9084, 12-Bit-ADC bis 20 GSPS, 16-Bit-DAC bis 28 GSPS |
| Momentanbandbreite | etwa 20 MHz über USB, intern 40 MSPS | bis 10 GHz pro Kanal im 2T2R-Modus des AD9084 |
| Host | USB 2.0, etwa 0,32 Gbit/s Nutzdaten | USB 3.2 Gen 2×2, etwa 17,6 Gbit/s, plus zwei QSFP-DD mit je 400GbE |
| Duplex | Halbduplex, ein Port | Vollduplex, zwei Kanäle, getrennte RX- und TX-Stecker |
| Takt | 25-MHz-TCXO, Si5351C, Analogmultiplexer | 100-MHz-OCXO, LMK5C33216, ADF4382A direkt auf den Wandler |
| Logik | iCE40UP5K und LPC4330 | Versal Premium XCVP1802, USB-Gerät ist ein FX20 |
| Lage | 6 Lagen FR4, ENIG | 14 Lagen, Rogers RO3003 auf Megtron 8, EPIG, VIPPO, Backdrill |
| Versorgung | 5 V über USB, wenige Watt | USB-PD 3.1 EPR, 48 V / 5 A, oder 48-V-Hohlstecker |

Die Analyse steht in [docs/ANALYSE.md](docs/ANALYSE.md). Die Schaltung, das Stackup und das, was diese Revision bewusst noch nicht ist, stehen in [docs/ARCHITEKTUR.md](docs/ARCHITEKTUR.md). Die Stückliste ist [docs/BOM.csv](docs/BOM.csv). Das Repository ignoriert `*.csv`; die Datei ist deshalb mit `git add -f` versioniert. KiCad-Projekt: [hardware/hackrf-ultra.kicad_pro](hardware/hackrf-ultra.kicad_pro).

`tools/gen_hardware.py` erzeugt Schaltplan, Platinenrahmen, Projektdatei und Stückliste neu. Die erzeugten Dateien sind eingecheckt.

## Lizenz

HackRF Ultra steht unter der CERN Open Hardware Licence Version 2, permissive Variante, wie die Lizenzdatei im Wurzelverzeichnis dieses Repositories. Die Analyse beschreibt HackRF Pro. Dieses Design bleibt Copyright Great Scott Gadgets und unter derselben Lizenz. Ultra kopiert die Praline-Schaltpläne nicht.

## Senden

Der Sender kann am PA-Ausgang eine P1dB von +32 dBm erreichen. Ob davon am Stecker etwas ankommt, misst man. Der PA ist ohne Schlüssel und ohne Freigabe aus. Wer sendet, hält sich an das Recht seines Standorts. Dieses Projekt beschreibt keine Anwendung dafür.
