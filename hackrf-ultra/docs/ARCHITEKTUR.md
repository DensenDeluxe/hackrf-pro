# HackRF Ultra, Architektur 0.1

Ultra tastet Hochfrequenz direkt ab. Die Zwischenfrequenz von Praline, der RFFC5072, der MAX2831, die Spiegelfilterbank und der Si5351 kommen nicht mit. Sie waren die Lösung für einen 8-Bit-Wandler bei 40 MSPS. Der Wandler hier ist ein Analog Devices AD9084, Apollo MxFE, Datenblatt Rev. D: vier 12-Bit-ADCs bis 20 GSPS, vier 16-Bit-DACs bis 28 GSPS, analoge Bandbreite bis 18 GHz, JESD204C bis 28,21 Gbit/s.

Beschaltet ist er als 2T2R.

| Wandler | Pfad |
|---|---|
| ADC0, ADC2 | gleichspannungsgekoppelt, 9 kHz bis 6 GHz, einer pro Kanal |
| ADC1, ADC3 | Balun, 6 GHz bis 18 GHz, einer pro Kanal |
| DAC0, DAC1 | die beiden Sender |
| DAC2 | Kalibrierton, im Wandler, nicht auf einen Stecker geführt |
| DAC3 | abgeschlossen, Reserve |

Die Momentanbandbreite von 10 GHz gilt im 2T2R-Modus des Bausteins pro Kanal, nicht als Versprechen, dass beide Kanäle diese Breite gleichzeitig aus einem einzigen Host-Port kommen. Die Rechnung steht unten.

## Empfänger

Pro Kanal eine 2,92-mm-Buchse, Kantenmontage, 40 GHz spezifiziert, eingesetzt bis 18 GHz. Die genaue Bestellnummer von Rosenberger oder Southwest Microwave wird festgenagelt, wenn die Launch-Simulation auf 127 µm RO3003 und 2,2 mm Plattendicke steht. Vorher eine Nummer zu raten erzeugt einen falschen Footprint.

Direkt an der Buchse ein Analog Devices ADGM1004, MEMS-SP4T, Gleichspannung bis 13 GHz. Ohne Versorgung sind die Kontakte offen. Das ist der Ruhezustand, nicht ein Default-Register. Jeder HF-Pin braucht einen Gleichstrompfad, sonst widerspricht die Schaltung dem Datenblatt. Dafür liegen 100 kΩ nach Masse an den sonst nur wechselspannungsgekoppelten Knoten.

Die vier Würfe:

1. **9 kHz bis 10 MHz.** Kein ADL9005. Dessen Datenblatt beginnt bei 10 MHz. Der Pfad geht in einen ADL5569, gleichspannungsgekoppelt, Gleichtakt vom AD9084 (`VCM_ADC0` beziehungsweise `VCM_ADC2`). Das SE-nach-Diff-Netzwerk ist die Schaltung aus dem ADL5569-Datenblatt, auf RO3003 nachsimuliert.
2. **10 MHz bis 6 GHz.** MACOM MADL-011023 als zweistufiger Shunt-Begrenzer, dann ADL9005 (NF typisch 2,5 dB von 0,01 bis 14 GHz, +17,5 dB), dann ADRF5720, dann Vierfach-Vorselektion.
3. **Übergabe an den Mikrowellenpfad.** Serienkondensator, weil der folgende Schalter erst bei 100 MHz anfängt.
4. **Schleife.** 20-dB-Koppler aus dem eigenen Sender. Im Ruhezustand nicht angewählt.

Der ADRF5720 ist die Variante von 9 kHz bis 40 GHz, 0,5-dB-Schritte, 31,5 dB. Der ADRF5730 sieht gleich aus und beginnt erst bei 100 MHz. Der wäre hier falsch.

Die Vorselektion im HF-Pfad ist ein zweiter ADGM1004: 9 kHz–30 MHz, 30–500 MHz, 0,5–2 GHz, 2–6 GHz. Filter sind Knowles-DLI-Dünnschicht oder, ganz unten, elliptische LC-Glieder auf RO3003. Die Übertragungsfunktion ist ein Layout-Ergebnis, keine aus Praline übernommene 0201-Kette. Deren Werte gelten für eine 2,4-GHz-Zwischenfrequenz.

Der Mikrowellenpfad nutzt einen ADRF5048, Silizium-SP4T, 100 MHz bis 45 GHz, nicht reflektierend, 1,4 dB typisch bei 18 GHz, Isolation typisch 41 dB bei 18 GHz. Würfe: Tiefpass 6–10 GHz (erste Nyquist-Zone bei 20 GSPS), Bandpass 10–14 GHz, Bandpass 14–18 GHz, und ein Durchgang, den nur Software mit einer Sperre öffnet. Dahinter ADL9005, ADRF5720, dann der Balun in den zweiten ADC. Der Balun ist das Netzwerk aus UG-2300, neu simuliert, weil das Dielektrikum nicht das der Evaluation-Platine ist. Eine erfundene Dash-Nummer wäre ein falsches S-Parameter-File.

Zwischen 100 MHz und 6 GHz existieren beide Pfade. Welcher besser ist, entscheidet die Kalibrierung im FPGA, nicht eine Lötbrücke.

Der Begrenzer hat ein Ziel, keine Messung: +30 dBm Dauerstrich überstehen, nachgewiesen auf einem Coupon derselben Pressung. Unter 10 MHz wirkt eine PIN-Diode schlecht. Dort schützt der direkte Pfad über den ADL5569 und eine kleinkapazitive Klemme, nicht der Begrenzer.

Die Systemrauschzahl ist die des ADL9005 plus Begrenzer, Schalter und Filter. Sie wird gemessen. 2,5 dB NF des nackten Verstärkers ist nicht die Zahl des Geräts.

## Sender

Ein HMC998APM5E pro Kanal, verteilter GaAs-pHEMT, Gleichspannung bis 22 GHz, P1dB +32 dBm, typisch 15 dB, 15 V, 500 mA Ruhestrom. Das ist ein Verarmungs-FET. Drain ohne negative Gatespannung zerstört ihn.

Die Vorspannung macht ein HMC980LP4E. Er erzeugt die negative Gatespannung selbst, legt erst Gate und dann Drain an, und regelt den Drainstrom auf den Wert, den der Messwiderstand vorgibt. Der Widerstand folgt der Formel im HMC980-Datenblatt für 500 mA. Er wird nicht geschätzt. Der +15-V-Regler speist nur den HMC980, nie das Drain des PA direkt.

Freigabe ist ein 74LVC1G08. Beide Eingänge haben Pulldown:

- `TX_ARM` kommt über einen Schlüsselschalter aus einer strombegrenzten Quelle. Offen heißt niedrig. Software kommt an diesem Schalter nicht vorbei.
- `TXA_EN` oder `TXB_EN` kommt aus dem FPGA, und die Pins liegen im Konfigurationszustand auf Pulldown.

Der Alarm des HMC980 ist `TXA_FAULT` beziehungsweise `TXB_FAULT`. Die LED `TX` hängt an `PA_EN`, also an der tatsächlichen Freigabe, nicht an einem Softwarebit.

Vor dem PA liegt ein ADRF5720. Der DAC kommt differenziell aus dem AD9084, durch einen Balun derselben Familie wie im Empfänger.

Ein 20-dB-Richtkoppler, Gleichspannung bis 26,5 GHz, Marki-Klasse, zweigt auf den Schleifenwurf des Empfangs-MEMS. Der isolierte Port ist mit 50 Ω abgeschlossen. Die genaue Bestellnummer folgt dem Layout, nicht umgekehrt.

Es gibt keinen gemeinsamen Antennenstecker. 41 dB Isolation bei 18 GHz trennen einen Sender mit +32 dBm P1dB nicht von einem Empfänger. Eine Antenne braucht einen externen Zirkulator oder Koppler. Zwei 2,92-mm-Buchsen pro Kanal, RX und TX, sind die ehrliche Konsequenz aus Vollduplex.

## Takt

Eine Wurzel, kein Multiplexer im Pfad.

Der OCXO ist ein Quarz von Wenzel, Reihe Sprinter, 100,000 MHz, Sinus, +13 dBm, 12 V. Die Bestellnummer wird gegen diese Maske gekauft, nicht erfunden: −130 dBc/Hz bei 100 Hz, −160 dBc/Hz bei 10 kHz, Boden bei oder unter −175 dBc/Hz. Ein MEMS-Oszillator gewinnt diese Maske im Nahbereich nicht. Deshalb steht hier keiner.

Der OCXO speist einen LMK5C33216. Dessen BAW-APLL liegt bei etwa 40 fs RMS an einem 491,52-MHz-Ausgang und hängt, einmal eingerastet, nicht am Referenzjitter. Der 10-MHz-SMA diszipliniert den LMK. Er wird nicht auf den Wandlertakt durchgeschaltet. CLKOUT ist 10 MHz aus einem LVCMOS-Ausgang, 33 Ω in Serie. PPS ist ein eigener SMA und der Trigger. Praline hat Takt und Trigger auf dieselben zwei SMA gemultiplext. Das ist hier aufgetrennt.

Aus dem LMK kommt die Referenz für einen ADF4382A. Dessen VCO läuft fundamental von 11,5 bis 21 GHz, etwa 20 fs integriert bei 20 GHz, PFD bis 625 MHz. Der AD9084 nimmt einen direkten RF-Takt von 8 bis 20 GHz, wechselspannungsgekoppelt, um +5 dBm, 100 Ω on-die (Rev. D, Tabelle 7). Der ADF4382A trifft dieses Fenster ohne Verdoppler. Der interne PLL des Wandlers bleibt aus. Das ist der jitterärmere Weg.

Ein LMX1214 verteilt den Takt. Additiver Jitter im Band etwa 5 fs, Rauschboden etwa −161 dBc/Hz bei 6 GHz. Ausgang 0 ist `CLK_P`/`CLK_N` zum AD9084. Ausgang 1 ist ein Messpunkt. SYSREF für JESD204C Subclass 1 kommt aus dem LMK, nicht aus dem Mikrowellen-PLL.

Eigene LDOs, alle LT3045: 3,3 V für den LMK, 5 V und 3,3 V für den ADF4382A, 2,5 V für den LMX1214. Der 1,0-V-Taktbereich des AD9084 (`P1V0_CK`) ist ebenfalls ein LT3045, gespeist aus der 1,0-V-Sammelschiene, nicht aus ihr direkt.

## Datenpfad

JESD204C, bis zu 16 Lanes je Richtung, Netze `JESD_ADC_P0..15` und `JESD_DAC_P0..15` samt Komplement. Der AD9084 hat 48 physikalische Lanes. Die nicht geführten werden nach UG-2300 abgeschlossen. Welche Lane auf welcher Kugel und welchem GTM-Pin liegt, schreibt das Constraint-File nach der Kanalsimulation. Diese Revision erfindet die Kugelnummern nicht.

Das FPGA ist ein AMD Versal Premium XCVP1802, derselbe Baustein wie auf dem VPK180, damit die GTM-Zahl keine Schätzung ist: 16 Empfangs- und 16 Sende-Lanes bei 28,21 Gbit/s NRZ, plus 8 Lanes bei 112 Gbit/s PAM4. Ein kleineres Premium-Gerät darf nur hinein, wenn seine GTM-Tabelle denselben Vertrag erfüllt. Geschwindigkeitsgrad und Gehäuse folgen dem Kanalverlust, nicht einem Katalogbild. Der ARM-A72 im PS führt das Gerät. Ein LPC4330 hätte hier nichts zu tun, was der PS nicht täte. Der iCE40UP5K hätte den Link nicht aufgemacht.

Host, zwei Wege:

**USB-C, Infineon EZ-USB FX20 (CYUSB402x, Datenblatt 002-33684 Rev. J).** USB 3.2 Gen 2×2, Nutzdaten laut Produktkurzinfo etwa 17,6 Gbit/s. Die LVDS-Seite des FX20 empfängt nur. 16 Lanes mal 1,25 Gbit/s tragen den Strom vom FPGA zum Host. Der Rückweg, Host zum FPGA, ist der 32-Bit-LVCMOS-Bus bei 80 MHz DDR:

32 bit × 80 × 10^6 × 2 = 5,12 Gbit/s.

Ein komplexes 16-Bit-Sample sind 32 Bit. Über USB gehen damit etwa 160 MSPS komplex hinaus zum Sender. Herein, auf der LVDS-Seite, tragen 17,6 Gbit/s etwa 550 MSPS komplex bei 16 Bit, mehr wenn man 12 Bit packt. Das ist der Laptop-Anschluss. Er ersetzt USB 2.0. Er ersetzt nicht die Bandbreite des Wandlers.

**Zwei QSFP-DD, je 400GbE.** Vier Lanes PAM4 mit 112 Gbit/s, direkt aus den GTM, ohne PHY. Ein Retimer-Footprint der 400G-Klasse liegt im Plan und bleibt unbestückt, solange die Augenöffnung auf Megtron 8 das nicht verlangt.

12 Bit komplex bei 10 GHz Momentanbandbreite:

10 × 10^9 × 2 × 12 = 240 Gbit/s.

Das passt in einen 400G-Port, 16 Bit wären 320 Gbit/s und hängen am Overhead. Der dokumentierte Vollratenmodus ist deshalb 12 Bit gepackt, ein Kanal, ein Port. Beide Kanäle gleichzeitig bei 10 GHz sind 480 Gbit/s und brauchen beide Ports. Ein einzelner 100G-Port hätte schon einen Kanal nicht getragen. Deshalb ist der Port 400G, und deshalb sind es zwei.

DDR5-5600, 8 GByte, fängt ab und trägt das PS. Boot aus einem Micron MT35XU02G, 2 Gbit Octal-SPI, und einer microSD fürs Feld. JTAG ist der 2×7-Header mit 1,27 mm, Versal-Belegung.

SPI zu den HF-Schaltern und Dämpfungsgliedern, I²C zum LMK und zum PD-Controller, SPI zum ADF4382A und LMX1214 sind eigene Busse. Sie teilen sich nicht die Sample-Leitungen.

## Versorgung

Praline holt sich 5 V aus USB und verteilt sie mit einem 800-mA-Doppelregler. Ultra verhandelt mit einem TPS26750 USB-PD 3.1 EPR, bis 48 V und 5 A, 240 W. Der TPS26750 verträgt diese 48 V nicht auf seinem eigenen VBUS-Pin. Dazwischen sitzt ein TPD4S480, Kurzschluss- und Pegelschutz, und schaltet über einen externen 100-V-MOSFET BSC040N10NS5. Das Gatenetz ist die TI-Referenz TIDT407, nicht eine freihändig gezeichnete Gateschaltung. Ein verriegelbarer 48-V-Hohlstecker liegt parallel, gemischt über einen LT8672. Ohne 240-W-Netzteil läuft das Gerät am Stecker.

Budget, keine Messung:

| Verbraucher | Ansatz |
|---|---|
| AD9084 | 40 W. Die Stromtabelle in Rev. D bei 1,25 GSPS summiert die 1,0-V-Domains schon auf etwa 10 A. 20 GSPS liegen darüber. 40 W ist der Topf, bis die Power-Estimator-Datei existiert. |
| XCVP1802 | 80 W, bis der XPE-Lauf auf diesem Design steht. |
| Zwei PA, gleichzeitig | 15 V × 0,5 A × 2 = 15 W an den HMC980, vor dem Wirkungsgrad. |
| OCXO, kalt | 5 W |
| Zwei 400G-Optiken und der FX20 | 20 W |
| Summe Last | etwa 160 W |
| Nach 90 % Reglerwirkungsgrad | etwa 180 W aus 48 V, Spitze im Budget 200 W |

240 W lassen Reserve. 5 V aus einem USB-2.0-Port tun das nicht. Deshalb ist der PD-Controller wieder da, den Praline bewusst entfernt hat.

Regler, alle Analog Devices, Silent Switcher oder µModule, wo der Strom es verlangt:

| Schiene | Regler | Kommentar |
|---|---|---|
| 0,80 V Kern | LTM4700 | FPGA, 100-A-Klasse |
| 0,88 V GTM | LTM4657 | eigene Schiene, eigene Einschaltreihenfolge |
| 1,0 V Sammler | LTM4658 | danach Ferrite |
| 1,0 V Takt des AD9084 | LT3045 | nur diese Domain, Strom passt in 500 mA |
| 1,8 V, 3,3 V, 5 V | LTM8074 | |
| 12 V OCXO | LT8642S | |
| 15 V PA | LT8642S | nur in den HMC980 |
| −5 V roh | ADP5070 | |
| −3,3 V | LT3094 | ADRF5048 und ADRF5720 brauchen die negative Schiene |
| 3,3 V Takt, 5 V und 3,3 V PLL, 2,5 V Puffer | LT3045 | |
| 1,5 V Aux | LT3045 oder ein µModule | wenn der Versal-Strom aus dem LDO läuft, bleibt es der LT3045, sonst wird es ein Modul. Das entscheidet der XPE-Lauf. |

Die 1,0-V-Domains des AD9084 bleiben getrennt: `P1V0_ADC`, `P1V0_ADCBK`, `P1V0_DAC`, `P1V0_DACDIG`, `P1V0_CK`. `P1V0_ADCBK` ist der Multi-Ampere-Zweig und bekommt keinen LDO. Die SERDES-Spannung heißt im Plan `P0V9_SERDES`. Die Zahl wird aus Tabelle 3, Rev. D, übernommen, bevor Kupfer gezeichnet wird. Bis dahin ist es ein eigener Regler, kein Mitversorger der ADC-Schiene.

`P5V0_RF` und `P3V3_RF` sind über stromfeste Ferrite von den Digitalschienen getrennt. Ein 0603-Signal-Ferrit ist hier der falsche Baustein.

Nichts außer dem PD-Controller startet von selbst. Die Enable-Netze kommen aus einem ADM1266. Dessen Zustandsautomat ist die Einschaltreihenfolge aus dem Versal-Power-Diagramm für dieses Gerät und aus UG-2300 für den Wandler, in das EEPROM geschrieben und auf der Bank geprüft, bevor die PA-Sicherung bestückt wird. Der ADM1266 schreibt Fehler mit. Ein INA228, 20 Bit, bis 85 V, sitzt auf dem 48-V-Eingang und je einer auf dem PA-Drain.

`P3V3_ALWAYS` ist die kleine Schiene, die der TPS26750 im Dead-Battery-Fall selbst erzeugt, damit er verhandeln kann, bevor 48 V existieren.

## Platine

14 Kupferlagen, Zieldicke 2,2 mm ±8 %.

Außenkupfer 0,5 oz, 17 µm, HVLP. Darunter ein Rogers-RO3003-Kern, 127 µm, εr 3,00, tan δ 0,0010. Das ist die HF-Referenz gegen Lage 2, eine durchgehende Masse. Der Rest ist Panasonic Megtron 8, εr etwa 3,1, tan δ etwa 0,0014, abwechselnd 100 µm Prepreg und 200 µm Kern, so dass die Platte auf 2,2 mm kommt. Die genauen Pressdicken liefert der Hersteller mit dem Coupon. Die Nennwerte im KiCad-Stackup sind der Auftrag, nicht das Messergebnis.

Oberfläche EPIG, nicht ENIG. Die Nickelschicht von ENIG kostet bei 18 GHz und bei 112 Gbit/s PAM4 messbar Dämpfung. Lötstopp wird von den HF-Leitungen um 0,15 mm zurückgezogen. Die Leitung ist dort nackte Mikrostreifenleitung.

Via-in-Pad, kupfergefüllt, überplattet. Laser-Microvias 75 µm, wo ein Blindvia kürzer ist als ein durchgehendes Via. Durchkontaktierungen in den 28-Gbit/s- und 112-Gbit/s-Netzen werden zurückgebohrt, Reststummel höchstens 0,15 mm. IPC-6012 Klasse 3 für die Platte, IPC-6018 Klasse 3 für die HF-Lagen. Jedes Panel bekommt einen Impedanzcoupon, einen Schliff und einen IST an den Vias.

Startwerte, am Coupon zu korrigieren, nicht als endgültige Breite zu verstehen:

| Klasse | Ziel | Start |
|---|---|---|
| RF_50, Lage 1 gegen Lage 2 | 50 Ω, unsymmetrisch | 0,26 mm auf 127 µm RO3003, εr 3,0, 17 µm Kupfer. Lötstopp liegt nicht auf der Leitung. |
| JESD_100, Streifenleitung Lage 3 | 100 Ω differentiell | 0,12 mm, Abstand 0,15 mm, nach der Pressung neu |
| GT_112 | 100 Ω differentiell, 112 Gbit/s | eigene Klasse, kürzerer Stummel, kein Nickel |
| USB_90 | 90 Ω differentiell | SuperSpeed des USB-C |

Toleranz ±5 %. Die KiCad-Netzklassen tragen diese Startwerte.

Abmessung des Rahmens: 280 mm × 190 mm. Sechs M3-Bohrungen, drei Fiducials. Höfe für AD9084 (24 mm × 26 mm), FPGA (50-mm-Umriss, bis die Gehäusezeichnung ihn ersetzt) und OCXO sind nur Umrisse auf F.Fab, ohne Kupfer, und in der BOM als mechanisch ausgeschlossen. Wer diese Datei an eine Platinenfertigung gibt, fertigt einen Rahmen ohne Bauteile. Der Siebdruck sagt das.

Hohlräume, gefräst, mit leitfähiger Dichtung und Absorber im Deckel über dem Takt: RX A, TX A, RX B, TX B, Takt (OCXO, LMK, ADF4382A, LMX1214). Der Wandler und das FPGA sitzen außerhalb dieser Dosen, der analoge Teil des AD9084 unter eigenem Deckel. Ein einzelner 2-Zoll-Rahmen wie auf Praline fasst das nicht.

## Was 0.1 nicht ist

- Kein Ball-Map und kein Land-Pattern. Pin-Nummern in den Symbolen sind Funktionsnummern. Die Zuordnung zur Kugel entsteht aus dem Datenblatt Rev. D und dem Versal-Package, nach der Simulation.
- Keine entkoppelte Stückliste der 0201 am BGA. Die Netzwerke stehen in UG-2300, im LTM4700-Datenblatt und im LT3045-Datenblatt und werden dort abgeschrieben, nicht neu erfunden.
- Keine gefilterte Übertragungsfunktion. Jedes Filter ist ein Bauteil mit Sollband. Die Dimensionierung ist ein EM-Lauf auf dem gepressten Stackup.
- Kein Gerber, kein Bestückungsdruck, kein getestetes Gerät.
- Keine Software, die `libhackrf` spricht. Das Protokoll ist neu, weil der Bus neu ist. Ein Kompatibilitätsmodus, der 20 MSPS mit 8 Bit über USB anbietet, ist eine Firmwarefrage und kein Grund, den MAX5865 zu behalten.
- Kein PortaPack. Die Stiftleiste, die 5-V-Versorgung und das Gehäuse von Pro passen hier nicht hin.

`tools/gen_hardware.py` schreibt das KiCad-Projekt neu. Wer am Netzvertrag etwas ändert, ändert das Skript und erzeugt die Dateien neu, statt nur eine der beiden Seiten anzufassen.

## Senden

Der PA kann +32 dBm an seinem Ausgang abgeben. Das ist mehr als ein Laborkabel sorglos verträgt, und es ist ein Sender im Sinne des Funkrechts. Der Schlüssel ist zu, die Pulldowns halten die Freigabe niedrig, der HMC980 legt ohne Freigabe kein Drain an. Wer eine Antenne anschließt, kennt die Zuteilung an seinem Standort. Dieses Dokument beschreibt den Aufbau, keine Anwendung.
