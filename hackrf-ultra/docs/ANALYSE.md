# Analyse HackRF Pro, Revision 1.2.1

Gegenstand ist der Schaltplan und das Layout in diesem Repository, Stand `d81df76`, Revision 1.2.1, Codename Praline. HackRF Pro ist ein halbduplexer Transceiver von 100 kHz bis 6 GHz, abstimmbar bis etwa 7,1 GHz, mit 8-Bit-I/Q und bis zu 20 MSPS über USB 2.0. Intern läuft der Wandler mit bis zu 40 MSPS. Erweiterte Präzision liefert nach starker Dezimierung 16-Bit-Wörter bei typisch 9 bis 11 effektiven Bit. Halbe Präzision liefert 4 Bit bei bis zu 40 MSPS.

Die elf Blätter sind Microcontroller, IF Transceiver, RF Front End, ADC/DAC, Power, USB, Mixer, Clock Generator, Switch Control, FPGA und Image Reject Filters. Die Platine hat sechs Kupferlagen, 1,58 mm, ENIG.

## Warum die Hochfrequenz so gebaut ist

Ein einzelner billiger Basisbandwandler kann 100 kHz bis 6 GHz nicht sehen. Praline löst das mit zwei Umsetzungen, wie schon HackRF One, nur mit anderen Bausteinen.

1. Der RFFC5072 (U4, Blatt Mixer) mischt die Antennenfrequenz auf eine feste Zwischenfrequenz um 2,4 GHz. Sein integrierter Synthesizer und Mischer sind bis 6 GHz spezifiziert. Darüber wird die Abstimmung unsicher. Die Dokumentation von Great Scott Gadgets nennt 7,1 GHz als Obergrenze, die zuverlässig noch funktionieren soll, und 7,25 GHz als Versuch, der scheitern kann.
2. Der MAX2831 (U17, Blatt IF Transceiver) ist ein WLAN-Transceiver für 2,3 bis 2,6 GHz. Er mischt die Zwischenfrequenz auf Gleichlage, filtert und verstärkt das Basisband. Zwei Pulse-Electronics-Bandpässe BPF1608LM02R2400A und zwei TDK-Baluns TFSZ06052460-3310A2X halten ihn in seinem Band.
3. Liegt die Nutzfrequenz schon im Band des MAX2831, wird der RFFC5072 umgangen. Dafür gibt es den Pfad `MIX_BYPASS`.

Die Spiegelfrequenz des ersten Mischers wird nicht rechnerisch unterdrückt, sondern weggefiltert. Das Blatt Image Reject Filters schaltet mit einem Maxscend MXD8546F (U1, DPDT) und einem MXD8638C (U9, SP3T) zwischen Tiefpass, Hochpass und Bypass. Die konzentrierten Werte liegen bei 1,6 nH bis 5,6 nH und 0,7 pF bis 1,8 pF, alles 0201 von Murata. Die letzten Commits haben genau diese Werte angefasst (`Correct C56, L14 reference designator positions`, davor Bauteiländerungen). Das ist Handabstimmung einer diskreten Filterbank, kein fertiges Dünnschichtfilter.

Dieselbe Filterbank wird für Senden und Empfangen in entgegengesetzter Richtung benutzt. Das Blatt Switch Control erzeugt die Polarität mit 74LVC1G86 (XOR), 74LVC1G08, 74LVC1G32 und einem 74HC00. Die Netznamen `RX_XOR_MIX`, `RX_XOR_LPF`, `LPF_OR_MIX_BYPASS`, `MIX_EN` und `TX_MIX_EN` sind diese Logik. Sie ist klein, fest verdrahtet und für 40 MSPS schnell genug. Sie ist auch der Grund, warum jeder neue Pfad ein neues Gatter braucht.

## Empfangspfad

Der Antennenstecker P3 ist eine SMA-Buchse von MyAntenna, Kante, 50 Ohm. Davor sitzt Schutz, nicht Verstärkung: eine bidirektionale TVS PESD5V0H1BSF von Nexperia, die PIN-Diode BAR9002 von Infineon und eine Schottky PMEG4010. HackRF One war bei etwa −5 dBm am Eingang am Ende. Pro verbessert den Schutz, bleibt aber ein Kleinsignal-Frontend. Ein +30-dBm-Signal ist kein Auslegungsfall.

Dahinter teilt ein MXD8638C (U12, SP3T) auf Empfangsverstärker, Sendezweig und Bypass auf. Der erste Empfangsverstärker ist ein BGB741L7ESD von Infineon, spezifiziert von 50 MHz bis 3,5 GHz. Der zweite ist ein TRF37C73 von Texas Instruments, 1 MHz bis 6 GHz. Unter 50 MHz trägt der BGB741 nichts, über 3,5 GHz bricht er ein. Die 0,3-pF-Kondensatoren C209 und C188 sind Abstimmelemente genau an dieser Stelle. Der Commit `Tune RX RF amp` ist dieselbe Aussage im Git-Log.

Die Antennenspeisung kommt aus einem AP22652 mit 125 mA ±20 %, über 100 µH. Ein zweiter AP22652 auf dem Power-Blatt begrenzt 3V3AUX auf 235 mA.

Auf dem Mischer liegen Baluns TTM B0310J50100AHF, 50 auf 100 Ohm. Der Schleifenfilter des RFFC5072 ist mit 22,6 kΩ, 51 kΩ, 330 pF, 8,2 pF und 180 pF beschaltet. Ein zweiter BGB741 sitzt nur im Sendezweig des Mischers. Der Commit `Use mixer compensation amp only for TX` hat den Empfangspfad davon befreit.

## Basisband

Der MAX5865 (U18) ist ein analoges Frontend mit 8-Bit-ADC und 10-Bit-DAC bei 40 MSPS. Das ist der Grund für die internen 40 MSPS. Vier GT4227, eigentlich USB-2.0-Schalter, schalten das Antialiasing-Filter um. Das ist ein billiger analoger Multiplexer mit kleiner Kapazität, kein USB-Baustein an dieser Stelle.

Zwei Notizen auf dem Blatt sind der Beleg, dass das Basisband nicht symmetrisch verdrahtet ist, wie das Symbol es suggeriert:

- RXBB.Q+ und Q− sind getauscht. Das invertiert das Spektrum. Die Gateware dreht es zurück.
- TX-I und TX-Q sind getauscht, und ein Differenzpaar ist zusätzlich invertiert. Die beiden Inversionen heben sich auf.

Die Gleichtaktspannung ist 1,27 V, gesetzt über REFIN. DNP-Bestückung an mehreren Widerständen ist die Reserve für eine andere Gleichtaktlage.

Mehr Bits als acht entstehen hier nicht im Wandler. Sie entstehen durch Dezimierung in einem FPGA, das dafür kaum Platz hat.

## Digitalteil

Das FPGA ist ein Lattice iCE40UP5K-SG48ITR. 5280 LUT4, acht DSP-Blöcke, Gehäuse mit 48 Pins. Die Schnittstelle zum Wandler ist `DA[0..7]` vom ADC und `DD[0..9]` zum 10-Bit-DAC, mit 100-Ohm-Vorwiderständen in Netzwerken. Zum Mikrocontroller gehen 13 SGPIO-Leitungen. Konfiguration läuft über SPI (`CRESET`, `CDONE`, `SPI_CS`).

Der Mikrocontroller ist ein NXP LPC4330FET180, flashlos, USB 2.0 High-Speed. Der Boot-Strap ist SPIFI, die Taste SW1 zieht auf USB0-DFU. Der Flash ist ein Winbond W25Q32, 32 Mbit. Takt des Controllers ist ein 12-MHz-Quarz, die RTC ein 32,768-kHz-Quarz.

USB 2.0 High-Speed trägt praktisch etwa 40 MByte/s. 20 MSPS mal 8 Bit I und 8 Bit Q sind 40 MByte/s, also 0,32 Gbit/s. Damit ist das Kabel voll. 40 MSPS gehen nur noch, wenn man auf 4 Bit abschneidet. 16 Bit über dasselbe Kabel erzwingen eine Dezimierung um mindestens 16. Das steht so in der Gateware-Dokumentation und folgt aus dem Stecker.

Der USB-Stecker ist USB-C, aber nur USB 2.0: eine Buchse von DEALON, eine Gleichtaktdrossel Murata DLM0NSB280HY2D, TVS auf CC und auf den Datenleitungen. Der Commit `Use Type-C power instead of Type-C controller` hat den PD-Controller entfernt. CC ist passiv. Die Buchse liefert 5 V, sonst nichts.

Die Erweiterungsleisten P20, P22 und P28 bleiben die HackRF-Stiftleiste, unter anderem für PortaPack und Opera Cake. P22 führt einen zweiten Takteingang, getrennt vom SMA.

## Takt

X1 ist ein 25-MHz-TCXO von HCI, Typ 8122S-25.000NQ33FTL. Er speist einen Si5351C mit acht Ausgängen: Mikrocontroller, Frontend-Wandler, Mischer, MAX2831, FPGA, SCT und die beiden SMA. Das ist für 8 Bit bei 40 MSPS ein angemessener Takt. Es ist kein Takt für einen mehrbitigen GHz-Wandler.

P1 und P2 sind SMA und per 74HC4051 und 74LVC1G3157 umschaltbar zwischen Takteingang, Taktausgang und Trigger. Die Notiz auf dem Blatt sagt: 3,3-V-CMOS, 10 MHz, mit Firmwareänderung 10 bis 100 MHz am Eingang. Der Analogmultiplexer liegt im Taktpfad. Er ist bequem und er ist eine Quelle für Jitter und Nebenwellen. Trigger und Takt teilen sich dieselben Stecker. Ein sauberer PPS existiert nicht als eigener Port.

## Versorgung

Eingang ist VBUS oder ein zweiter Eingang VIN. Eine Überspannungssperre mit 5,6-V- und 6,2-V-Zenerdioden schaltet zwischen 5,5 und 6,0 V ab. Die Notiz sagt ausdrücklich, dass der Controller jeden Eingang trennen darf und die Überspannungssperre nicht abschaltbar ist.

Der Wandler ist ein TPS62410, ein doppelter 800-mA-Abwärtsregler. Daraus werden die digitalen Schienen, unter anderem 1,2 V für den FPGA-Kern. Zwei XC6206 in der 2,5-V-Festspannungsvariante, je 100 mA, erzeugen 2V5RF. Ferrite vom Typ 1 kΩ bei 100 MHz trennen analoge und digitale Inseln: VAA, 3V3FPGA, 3V3CLK, 3V3LED, 3V3AUX. Lastschalter sind wieder AP22652.

Das reicht für ein iCE40, einen LPC4330 und zwei kleine HF-Verstärker. Ein OCXO im Aufheizen, ein 15-V-PA mit 500 mA und ein Wandler mit mehreren Ampere auf 1,0 V passen in dieses Budget nicht. Die 100-mA-LDOs sind die harte Aussage.

## Layout

Kupfer: Außenlagen 35 µm, Innenlagen 15 µm. Dielektrikum: Prepreg 7628, 0,20 bis 0,21 mm, εr 4,4, tan δ 0,013, dazwischen FR4-Kerne 0,4 mm, εr 4,6, tan δ 0,02. Oberfläche ENIG. Lötstopp grün, auch über den HF-Leitungen.

Bei 6 GHz ist ein Verlustfaktor von 0,02 etwa eine Größenordnung schlechter als Rogers RO3003 oder Megtron 8. Das Glasgewebe von 7628 erzeugt darüber hinaus eine richtungsabhängige Laufzeit. ENIG trägt eine Nickelschicht, die ab einigen Gigahertz und erst recht bei 25 Gbit/s den Leiter extra dämpft. Sechs Lagen ohne Microvias und ohne Backdrill sind für diesen Wandler und diesen FPGA die richtige, günstige Wahl. Sie sind keine Wahl für 18 GHz oder für 112-Gbit/s-PAM4.

Die Kontur aus den Edge-Cuts-Koordinaten spannt ungefähr 120 mm mal 75 mm auf. Ein gestanzter Schirmrahmen, TE-Connectivity-Bauform 2 Zoll mal 1,5 Zoll, deckt den HF-Teil ab. Das ist ein einzelner Hohlraum, keine in Stege geteilte Dose über Takt, PA und Mischer.

Die Designregeln starten bei 0,127 mm Leiterbahn und Abstand. Das ist eine digitale Klasse, keine 18-GHz-Klasse.

## Was davon richtig ist und bleiben muss

- Der Empfänger muss einen starken Störer überleben, sonst ist die erste Feldmessung die letzte. Pro hat das gegenüber HackRF One verbessert und ist trotzdem noch ein Kleinsignalgerät.
- Senden ist ein privilegierter Zustand. Pro kann den Sendezweig in Hardware ausnehmen, nicht nur per Bit.
- Analog- und Digitalversorgung sind mit Ferriten getrennt. Der FPGA-Kern hat eine eigene Schiene und ein Enable.
- Ein externer 10-MHz-Takt und ein Trigger gehören an den Stecker, nicht nur auf eine Stiftleiste.
- Die RX/TX-Umschaltung hat einen definierten Ruhezustand.
- Der Schirm ist bestückt, nicht optional.

## Wo Nachbessern aufhört

Diese Grenzen verschwinden nicht durch ein anderes Filterglied oder einen leiseren LDO:

| Grenze | Wo sie im Plan steht | Was sie kappt |
|---|---|---|
| 8 Bit, 40 MSPS | MAX5865 | Dynamik und Abtastrate. Dezimierung im iCE40 holt auf Kosten der Bandbreite ein paar Bit nach. |
| Basisbandfilter des MAX2831 | WLAN-Transceiver, Kanalfilter im Chip | Die analoge Momentanbandbreite bleibt ein WLAN-Kanal, auch wenn der Wandler schneller getaktet wird. |
| USB 2.0 | LPC4330 und die Buchse ohne SuperSpeed | 0,32 Gbit/s. Darüber wird abgeschnitten oder dezimiert. |
| 5280 LUT4 | iCE40UP5K-SG48 | Kein JESD, kein breites FIR, RX- und TX-Gateware der hohen Präzision passen nicht gleichzeitig. |
| RFFC5072 | Mischer bis 6 GHz | 7 GHz ist der Rand, nicht ein Arbeitsband. |
| BGB741 bis 3,5 GHz | Empfangsverstärker | Die obere Hälfte des Bands hängt am TRF37C73 allein. |
| Si5351 plus 74HC4051 | Taktblatt | Jitter und Nebenwellen, die ein 8-Bit-Wandler verzeiht. |
| 5 V, 100-mA-LDOs | TPS62410, XC6206, kein PD | Kein OCXO, kein Watt-PA, kein dicker FPGA. |
| FR4 7628, ENIG, 6 Lagen | Stackup im Layout | Leitungsverlust und Gewebeschiefe ab einigen Gigahertz. |
| Ein Port, Halbduplex | eine SMA, Schalterbank | Ein Schalter mit 40 dB Isolation trägt keinen gleichzeitigen Sender und Empfänger. |

Ultra zieht daraus eine andere Architektur, nicht eine dichter bestückte Praline. Der ZF-Trick war die Antwort auf den MAX5865. Ohne diesen Wandler ist die Zwischenfrequenz Ballast: ein zweiter Synthesizer, eine Spiegelfilterbank, ein WLAN-Chip als zweite Mischstufe und eine analoge Logik, die das alles umschaltet.
