#Redispatch2.0-Daten (im XML-Format)
#per Email mit S/MIME signiert und verschlüsselt
#an RAIDA/Connect+ versenden - https://netz-connectplus.de

#Regelungen zum Übertragungsweg
#https://www.bundesnetzagentur.de/DE/Beschlusskammern/BK06/BK6_83_Zug_Mess/835_mitteilungen_datenformate/Mitteilung_21/EBD_%C3%9Cbertragungsweg_Konsultationsdokumente/Regelungen_zum_Uebertragungsweg_1_5.pdf?__blob=publicationFile&v=1

import os

import gzip
import shutil
from pathlib2 import Path

import socket
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from email.utils import formatdate
from email.utils import make_msgid

from smail import sign_message
from smail import sign_and_encrypt_message

import smtplib
import ssl
from datetime import datetime

## Konfiguration:

DEBUG = False

#in diesem Pfad werden die zu versendenden XML-Dateien abgelegt:
outpath = './xml-daten/'
#in diesem Pfad werden die versendenten XML-Dateien(gzip) und Emails archiviert:
archivepath = './xml-daten/archiv/'

#Absender S/MIME Privatekey und Zertifikat zum Signieren der Email
smime_privatekey = './certificates/your_private_smime_key.pem'
smime_cert_sender = './certificates/your_smime_certificate.crt'
#Absender Email-Adresse
send_from = 'your_redispatch@test.test'
#SMTP Server (SSL Port 465) zum Versenden der Emails an RAIDA/Connect+:
smtp_server = "your_mail_server.test.test"
smtp_login = 'your_redispatch@test.test'
smtp_password = "secret_password"

#Empfänger S/MIME Public-Certificate zum Verschlüsseln der Email:
if (DEBUG):
    #RAIDA Testsystem: https://netz-connectplus.de/home/tester/
    smime_cert_receiver = './certificates/smime_raida_test.crt'
    send_to = 'test@edv.raida.de'
else:
    #RAIDA Produktivsystem
    smime_cert_receiver = './certificates/smime_raida_prod.crt'
    send_to = 'prod@edv.raida.de'

#Logging und Fehlerbenachrichtigung:
logdir = './logs/'
logfile = logdir + 'log.txt'
#Email-Adresse und Emailserver zum Versand von Fehlermeldungen:
notify_email_to = "your_logging@test.test"
notify_email_from = "noreply@test.test"
#SMTP Server (SSL Port 465) zum Versenden der Fehlerbenachrichtigung:
notify_smtp_server = "your_mail_server.test.test"
notify_smtp_server_account = "noreply@test.test"
notify_smtp_server_password = "secret_password"

## Ende Konfigurationsabschnitt

errors = []

def addlog(text):
    global errors
    error = "[Date] {}, ".format(datetime.now()) + text
    errors.append(error)

def convert_list_to_string(org_list, seperator=' '):
    """ Convert list to string, by joining all items in list with given separator.
        Returns the concatenated string """
    return seperator.join(org_list)

def log():  # in datei speichern ( errors -> log.txt )
    global errors
    global logfile

    if len(errors) > 0:
        with open(logfile, "a") as f_logfile:
            f_logfile.write('\n'+convert_list_to_string(errors,'\n'))

def benachrichtigung(email,subject,body,emailcc=''): # email versenden
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = notify_email_from
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain = notify_email_from.split('@')[-1])
        
    notify_smtp_server_port = 465
    context = ssl.create_default_context()

    msg['To'] = email
    if emailcc != '' :
        msg['CC'] = emailcc
        
    try:
        with smtplib.SMTP_SSL(notify_smtp_server, notify_smtp_server_port, timeout=5,context=context) as server:
            server.login(notify_smtp_server_account, notify_smtp_server_password)
            server.send_message(msg)
    except smtplib.SMTPException:
        addlog('error - Emailversand an ' + email + ' fehlgeschlagen!')
    except socket.gaierror:
        addlog('error - Verbindung zu Mailserver ' + notify_smtp_server + ' fehlgeschlagen!')



def main():

    #Log-Verzeichnis erzeugen
    Path(logdir).mkdir(parents=True, exist_ok=True)

    #Archiv-Verzeichnis erzeugen
    Path(archivepath).mkdir(parents=True, exist_ok=True)

    try:
        with open(smime_privatekey) as privkeyfile:
            privkey = privkeyfile.read()
    except IOError:
        addlog('error - Private-Key ' + smime_privatekey + ' Lesen fehlgeschlagen!')
        #aufgelaufene Fehlermeldungen in Log speichern
        log()
        benachrichtigung(notify_email_to,"RAIDA - Fehler",convert_list_to_string(errors,'\n'))
        exit

    try:
        with open(smime_cert_receiver, 'rb') as pubcertfile:
            pubcert = pubcertfile.read()
    except IOError:
        addlog('error - Public-Key ' + smime_cert_receiver + ' Lesen fehlgeschlagen!')
        #aufgelaufene Fehlermeldungen in Log speichern
        log()
        benachrichtigung(notify_email_to,"RAIDA - Fehler",convert_list_to_string(errors,'\n'))
        exit


    #Liste von Dateien im "outpath" erstellen
    l_xmlfile = []
    for (dirpath, dirnames, filenames) in os.walk(outpath):
        l_xmlfile.extend(os.path.join(dirpath, filename) for filename in filenames)

    #jede gefundene Datei abarbeiten
    for (xmlfile) in l_xmlfile:
        print(xmlfile)
        #Dateinamen extrahieren
        xmlfile_fn = os.path.basename(xmlfile)
        lparts = xmlfile_fn.split('.')
        #Dateien, die kein XML sind, überspringen
        if lparts[-1] != 'xml':
            continue

        #Schritt1: Gzip
        #XML-Datei mit gzip komprimieren
        
        try:
            with open(xmlfile, 'rb') as f_in:
                with gzip.open(xmlfile + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
            addlog('error - Öffnen oder Speichern von ' + xmlfile + ' fehlgeschlagen!')
            continue

        #Schritt2: Base64 encode
        #Schritt3: Mail Container mit Anhang erzeugen
        #"Regelungen zum Übertragungsweg" - Kapitel 6.2 E-Mail-Anhang:
        #Der Anhang ist nicht separat zu verschlüsseln und auch nicht zu
        #signieren, da dies bereits durch S/MIME erfolgt.

        try:
            with open(xmlfile + '.gz', 'rb') as fil:
                #"Regelungen zum Übertragungsweg" - Kapitel 6.2 E-Mail-Anhang
                #Der Content-Type des MIME-Parts mit dem Anhang muss
                #Application/octet-stream sein.
                part_attachment = MIMEApplication(fil.read(),
                    name=xmlfile_fn + '.gz')
        except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
            addlog('error - Öffnen von ' + archivepath + xmlfile_fn + '.gz' + ' fehlgeschlagen!')
            continue

        # After the file is closed
        part_attachment['Content-Disposition'] = 'attachment; filename="%s"' % (xmlfile_fn + '.gz')
    

        #Schritt4: Signieren mit
        #Signaturverfahren (Signature algorithm): RSASSA-PSS (gemäß IETF RFC 4056)
        #Hashfunktion (Hash algorithm): SHA-256 oder SHA-512 (gemäß IETF RFC 5754).
        #siehe "Regelungen zum Übertragungsweg" - Kapitel 5.3 Algorithmen und Schlüssellängen für S/MIME

        #+Schritt5: Verschlüsseln mit
        #Inhaltsverschlüsselung (Content encryption): AES-128 CBC, AES-192 CBC
        #oder AES-256 CBC (gemäß IETF RFC 3565).
        #siehe "Regelungen zum Übertragungsweg" - Kapitel 5.3 Algorithmen und Schlüssellängen für S/MIME

        #Signieren und Verschlüsseln in einem Schritt: https://pypi.org/project/python-smail/

        #+Schritt6: Mail-Betreff etc.  setzen

        #"Regelungen zum Übertragungsweg" - Kapitel 6.4 E-Mail-Betreff
        #Der E-Mail-Betreff muss gleichlautend mit dem Dateinamen der [unkomprimierten] Datei
        #sein.  Dies schließt die Dateiendung ein [aber ohne .gz].  Zur Namenskonvention des Dateinamens siehe Kapitel
        #6.2 (E-Mail-Anhang). 
        #=> EDI@Energy-Dokument „Allgemeine Festlegungen“ - Kapitel 8.12 Namenskonvention für XML-Nachrichten
        #https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=1226&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=d72a6600538d02835f72c72526b8a13e


        message = MIMEMultipart()
        message['Date'] = formatdate(localtime=True)
        message['Message-ID'] = make_msgid(domain = send_from.split('@')[-1])
        message['From'] = send_from
        message['To'] = send_to
        message['Subject'] = xmlfile_fn
        message.attach(part_attachment)

        key_signer = smime_privatekey
        cert_signer = smime_cert_sender
        #Empfänger-Zertifikat
        cert = smime_cert_receiver

        try:
            signed_encrypted_message = sign_and_encrypt_message(message, key_signer, cert_signer, [cert], 
                                                            digest_alg="sha256",sig_alg="pss",
                                                            attrs=True, prefix="",
                                                            content_enc_alg="aes256_cbc")
        except Exception as e:
            addlog('error - sign_and_encrypt_message mit Error "' + repr(e) + '" fehlgeschlagen!')
            continue

        #DEBUG: signierten und verschlüsselten Mail Container abspeichern
        if DEBUG:
            try:
                with open(xmlfile + '.gz.b64.eml.sig.enc.eml', 'w', encoding='utf-8') as f:
                    f.write(signed_encrypted_message.as_string())
            except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
                addlog('error - Speichern von ' + xmlfile + '.gz.b64.eml.sig.enc.eml' + ' fehlgeschlagen!')
            except Exception as e:
                addlog('error - Speichern von ' + xmlfile + '.gz.b64.eml.sig.enc.eml' + ' mit Error "' + repr(e) + '" fehlgeschlagen!')


        #Schritt7: Versenden
        port = 465
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP_SSL(smtp_server, port, timeout=5,context=context) as server:
                server.login(smtp_login, smtp_password)
                server.sendmail(send_from,send_to,signed_encrypted_message.as_string())
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

                #DEBUG: unverschlüsselte Mail mit Anhang abspeichern
                if DEBUG:
                    with open(archivepath + timestamp + '_' + xmlfile_fn + '.gz.b64.eml', 'w', encoding='utf-8') as f:
                        f.write(message.as_string())

                #gesendete Email in Archiv ablegen
                try:
                    with open(archivepath + timestamp + '_' + xmlfile_fn + '.eml', 'w', encoding='utf-8') as f:
                        f.write(signed_encrypted_message.as_string())
                except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
                    addlog('error - Speichern von ' + archivepath + xmlfile_fn + '.eml' + ' fehlgeschlagen!')
                    continue

                #gesendetes XML.gz in Archiv verschieben
                try:
                    shutil.move(xmlfile + '.gz', archivepath + timestamp + '_' + xmlfile_fn + '.gz')
                except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
                    addlog('error - Verschieben von ' + xmlfile + '.gz' + ' fehlgeschlagen!')
                    continue

        except smtplib.SMTPException:
            addlog('error - Emailversand an ' + email + ' fehlgeschlagen!')
        except socket.gaierror:
            addlog('error - Verbindung zu Mailserver ' + smtp_server + ' fehlgeschlagen!')


    #aufgelaufene Fehlermeldungen in Log speichern
    log()

    if len(errors) > 0:
        benachrichtigung(notify_email_to,"RAIDA - Fehler",convert_list_to_string(errors,'\n'))


if __name__ == '__main__': 
    main()