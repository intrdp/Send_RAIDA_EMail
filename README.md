# Send_RAIDA_EMail
E-Mail Client zum Redispatch 2.0 konformen Datenversand an die RAIDA Plattform

RAIDA (<https://raida.de>) ist eine Plattform zum Datenaustausch für den Redispatch 2.0 von Connect+ (<https://netz-connectplus.de>),
die folgende Kommunikationswege bietet: E-Mail, SFTP, REST-WebService.

Wer den Kommunikationsweg "E-Mail" nutzen möchte steht vor dem Problem daß die, in den "Regelungen zum Übertragungsweg"
vorgeschriebenen, S/MIME Zertifikate und Verschlüsselungsverfahren von Standard-Email-Programmen wie Thunderbird oder Microsoft Outlook nicht unterstützt werden.

Aus diesem Grund entstand dieser kleine Email-Client, der eine Email entsprechend der Formatvorgaben der "Regelungen zum Übertragungsweg" und "Allgemeine Festlegungen zu den
EDIFACT- und XML-Nachrichten" erzeugt, signiert, verschlüsselt und versendet.

Signieren und Verschlüsseln übernimmt die hervorragende Bibliothek: <https://pypi.org/project/python-smail/>
Vielen Dank an die Authoren von Python SMAIL und dessen Vorgänger Projekt <https://github.com/balena/python-smime>

Zielgruppe von Send_RAIDA_EMail sind IT-erfahrene Betreiber von Solaranlagen oder anderen erneuerbaren Energieanlagen, die ihre Verpflichtung zum Datenaustausch im Redispatch 2.0 nicht an einen externen Dienstleister vergeben möchten, sondern dies selbst übernehmen wollen.

Send_RAIDA_EMail wird so wie es ist, ohne Support oder Garantie auf Vollständigkeit oder Richtigkeit zur Verfügung gestellt.

## Dokumente

["Regelungen zum Übertragungsweg"](https://www.bundesnetzagentur.de/DE/Beschlusskammern/BK06/BK6_83_Zug_Mess/835_mitteilungen_datenformate/Mitteilung_21/EBD_%C3%9Cbertragungsweg_Konsultationsdokumente/Regelungen_zum_Uebertragungsweg_1_5.pdf?__blob=publicationFile&v=1)

["Allgemeine Festlegungen zu den
EDIFACT- und XML-Nachrichten"](https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=1226&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=d72a6600538d02835f72c72526b8a13e)

## Bedienung

Der Datenaustausch im Redispatch 2.0 erfolgt mit XML-Dateien. Send_RAIDA_EMail übernimmt lediglich den Versand dieser XML Dateien. Erzeugt werden müssen die XML-Dateien anderweitig, z.B. mit Hilfe des RAIDA Agent - siehe https://www.raida-agent.de/startseite. Der RAIDA Agent bietet eine Funktionen zur Excel/XML-Konvertierung.

### Konfiguration

Am Anfang des Python Codes befindet sich eine Sektion mit diversen Variablen, die an den Benutzer angepasst werden müssen:

#### "DEBUG"

DEBUG = False
Emails werden an das RAIDA Produktivsystem verschickt.

DEBUG = True
Emails werden an das RAIDA Testsystem verschickt und es werden zusätzliche Debug-Files abglegt um die erzeugten Emails einsehen zu können.

#### "outpath"

In der Variable "outpath" wird der Pfad definiert in dem die zu versendenden XML-Dateien abgelegt müssen.
Send_RAIDA_EMail kann auch mehrere XML-Dateien auf einmal verarbeiten. Jede in "outpath" abgelegt XML-Datei wird in einer eigenen Email verschickt.

#### "archivepath"

in diesem Pfad werden die versendenten Emails und XML-Dateien (gzip-komprimiert) archiviert.

#### "smime_privatekey" und "smime_cert_sender"

In diesen Variablen definieren Sie ihren Absender S/MIME Privatekey und ihr S/MIME Zertifikat, die zum Signieren der Email benötigt werden.

#### "send_from"

Hier wird die Absender Emailadresse festgelegt. Diese muss der Emailadresse entsprechen für die das Absender S/MIME Zertifikat ausgestellt wurde.

#### "smtp_server", "smtp_login", "smtp_password"

Hier wird der Emailserver und Emailserver-Login zum Versand der der Emails an RAIDA/Connect+ definiert.
Der verwendete Emailserver muss SMTP über SSL auf Port 465 unterstützen!

#### "smime_cert_receiver" und "send_to"

In Variable "smime_cert_receiver" wird das S/MIME Zertifikat des Empfängers festgelegt, welches zum Verschlüsseln der Email verwendet wird.
In "send_to" wird die Empfänger Emailadresse angegeben.

Beide Variablen sind bereits mit den aktuell gültigen Zertifikaten und Emailadressen des RAIDA Produktivsystems bzw. RAIDA Testsystems vorbelegt.

Entsprechend der Einstellung der Variable "DEBUG" wird das RAIDA Produktivsystem bzw. RAIDA Testsystem als Empfänger ausgewählt.

#### "logdir" und "logdir"

legen Pfad und Dateiname zur Ausgabe von Fehlermeldungen fest.

#### "notify_*"

In den Variablen, die mit "notify_" beginnen, werden
Email-Adresse und Emailserver zum Versand von Fehlermeldungen festgelegt.
Der verwendete Emailserver muss SMTP über SSL auf Port 465 unterstützen!
