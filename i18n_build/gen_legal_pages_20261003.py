#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 Impressum / Privacy Policy 两页 × 7 语言（2026-10-03）

为什么必须做：审计发现全站**没有隐私政策、没有 Impressum**，而站点已有德语版在服务
德国买家 —— 德国 §5 DDG 要求商业网站必须有 Impressum（公司、代表人、地址、联系方式、
争议解决途径），欧盟 DSGVO 要求告知处理目的 / 接收方 / 权利与救济途径。
对 B2B 采购商而言这是**准入门槛**：合规部查不到 Impressum 就会判定供应商不可用。

做法：以各语言的 `faq.html` 作外壳（保证导航 / 页脚 / 语言切换器 / 脚本完全一致），
只替换 head（title / description / canonical / hreflang）与中间内容块。

⚠️ 未知的法律事实用 `［…］` 显式标出 —— 宁可不完整，也不能假装完整。
   欧盟 ODR 平台已于 2025-07-23 停止运营，Impressum 里不能再引用它（写错反而是过失）。

用法：python3 i18n_build/gen_legal_pages_20261003.py [--dry-run]
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["", "de", "ja", "ko", "fr", "it", "es"]
BASE = "https://fjsanfan.com"
F = {
    "name": "FUJIAN SANFAN Sports Products Co., Ltd.",
    "name_cn": "福建三梵体育用品有限公司",
    "addr": "No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang, Quanzhou, Fujian, China",
    "email": "zenglinggun@gmail.com",
    "wa": "+86 15959029082",
}
MAIL = '<a href="mailto:%s">%s</a>' % (F["email"], F["email"])
WA = '<a href="https://wa.me/8615959029082">%s</a>' % F["wa"]
OPERATOR = "<p><strong>%s</strong> (%s)<br />%s</p>" % (F["name"], F["name_cn"], F["addr"])

# ── Impressum：各语言文案（同一事实、不同表达）──────────────────────────────
IMPRINT = {
"en": {
 "title": "Imprint & Legal Information — SANFAN",
 "desc": "Legal notice (Impressum) under § 5 DDG and § 18 MStV for FUJIAN SANFAN Sports Products Co., Ltd.",
 "h1": "Imprint",
 "lead": "Legal information required under § 5 DDG (German Digital Services Act) and § 18 MStV.",
 "secs": [
  ("Operator of this website", OPERATOR),
  ("Legal representative", "<p>［TO BE COMPLETED: full name of the legal representative］</p>"),
  ("Responsible for content under § 18 MStV",
   "<p>［TO BE COMPLETED: full name and address of the person responsible for the content of this website］</p>"),
  ("Contact", "<p>Email: %s<br />WhatsApp: %s</p>" % (MAIL, WA)),
  ("Consumer dispute resolution",
   "<p>We are neither obliged nor willing to take part in dispute-resolution proceedings before a consumer arbitration board.</p>"),
  ("Jurisdiction / arbitration",
   "<p>［TO BE COMPLETED: governing law and place of jurisdiction, or an arbitration agreement, if you want one］</p>"
   "<p class=\"note\">Note: the EU Online Dispute Resolution platform (ODR) was discontinued on 23 July 2025 and must no longer be referenced.</p>"),
  ("Content note",
   "<p>All information on this website is provided as B2B product information. Availability, specifications, lead times and price changes remain subject to confirmation in the individual inquiry and in a written order confirmation.</p>"),
 ]},
"de": {
 "title": "Impressum & Rechtsangaben — SANFAN",
 "desc": "Impressum nach § 5 DDG und § 18 MStV für die FUJIAN SANFAN Sports Products Co., Ltd.",
 "h1": "Impressum",
 "lead": "Pflichtangaben nach § 5 DDG (Digitale-Dienste-Gesetz) und § 18 MStV.",
 "secs": [
  ("Anbieter dieser Website", OPERATOR),
  ("Vertreten durch", "<p>［ERGÄNZUNG ERFORDERLICH: vollständiger Name der Geschäftsführung］</p>"),
  ("Verantwortlich für den Inhalt nach § 18 MStV",
   "<p>［ERGÄNZUNG ERFORDERLICH: vollständiger Name und Anschrift der für den Inhalt dieser Website verantwortlichen Person］</p>"),
  ("Kontakt", "<p>E-Mail: %s<br />WhatsApp: %s</p>" % (MAIL, WA)),
  ("Verbraucherstreitbeilegung",
   "<p>Wir sind weder bereit noch verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>"),
  ("Gerichtsstand / Schiedsklausel",
   "<p>［ERGÄNZUNG ERFORDERLICH: anwendbares Recht und Gerichtsstand oder Schiedsklausel, falls gewünscht］</p>"
   "<p class=\"note\">Hinweis: Die EU-Plattform zur Online-Streitbeilegung (ODR) wurde zum 23. Juli 2025 eingestellt und darf nicht mehr genannt werden.</p>"),
  ("Inhaltlicher Hinweis",
   "<p>Alle Angaben auf dieser Website sind B2B-Produktinformationen. Verfügbarkeit, Spezifikationen, Lieferzeiten und Preisänderungen bleiben bis zur Bestätigung im konkreten Anfrage- und Auftragsbestätigungsverfahren vorbehalten.</p>"),
 ]},
"ja": {
 "title": "運営者情報・法的告知 — SANFAN",
 "desc": "FUJIAN SANFAN Sports Products Co., Ltd. の運営者情報と法令に基づく告知。",
 "h1": "運営者情報",
 "lead": "ドイツ §5 DDG および §18 MStV に基づく法定記載。",
 "secs": [
  ("このサイトの運営者", OPERATOR),
  ("代表者", "<p>［要記入：代表者氏名］</p>"),
  ("内容責任者（§ 18 MStV）", "<p>［要記入：このサイトの内容に責任を持つ者の氏名・住所］</p>"),
  ("連絡先", "<p>メール：%s<br />WhatsApp：%s</p>" % (MAIL, WA)),
  ("消費者紛争解決",
   "<p>当社は、消費者紛争解決委員会による紛争解決手続に参加する義務を負わず、参加の意思もありません。</p>"),
  ("管轄・仲裁",
   "<p>［要記入：準拠法および管轄裁判所、または仲裁合意の内容］</p>"
   "<p class=\"note\">注：EU オンライン紛争解決プラットフォーム（ODR）は 2025 年 7 月 23 日に終了しており、参照できません。</p>"),
  ("内容に関する注記",
   "<p>本サイトに記載する情報はすべて B2B 製品情報であり、在庫・仕様・納期・価格変更は、個別のbuds.sdkél és a written order confirmation をもって確定します。</p>".replace("buds.sdkél és a written order confirmation", "お問い合せおよび書面での注文確認").replace("は、個別の", "は、個別の")),
 ]},
"ko": {
 "title": "운영자 정보 및 법적 고지 — SANFAN",
 "desc": "FUJIAN SANFAN Sports Products Co., Ltd.의 운영자 정보 및 법적 고지.",
 "h1": "운영자 정보",
 "lead": "독일 §5 DDG 및 §18 MStV에 따른 필수 기재 사항.",
 "secs": [
  ("이 사이트의 운영자", OPERATOR),
  ("대표자", "<p>［작성 필요: 대표자 성명］</p>"),
  ("내용 책임자(§ 18 MStV)", "<p>［작성 필요: 이 웹사이트 내용에 책임지는 사람의 이름과 주소］</p>"),
  ("연락처", "<p>이메일: %s<br />WhatsApp: %s</p>" % (MAIL, WA)),
  ("소비자 분쟁 해결",
   "<p>당사는 소비자 분쟁 해결 절차에 참여할 의무도, 의사도 없습니다.</p>"),
  ("관할 및 중재",
   "<p>［작성 필요: 적용 법률 및 관할 법원 또는 중재 합의 내용］</p>"
   "<p class=\"note\">참고: EU 온라인 분쟁 해결 플랫폼(ODR)은 2025년 7월 23일 종료되어 인용할 수 없습니다.</p>"),
  ("내용 관련 고지",
   "<p>본 사이트의 모든 정보는 B2B 제품 정보이며, 재고·사양·납기 및 가격 변경은 개별 문의와 서면 주문 확인을 통해 확정됩니다.</p>"),
 ]},
"fr": {
 "title": "Mentions légales — SANFAN",
 "desc": "Mentions légales au titre de l'article 5 DDG et de l'article 18 MStV pour FUJIAN SANFAN Sports Products Co., Ltd.",
 "h1": "Mentions légales",
 "lead": "Informations obligatoires au titre de l'article 5 DDG et de l'article 18 MStV.",
 "secs": [
  ("Éditeur de ce site", OPERATOR),
  ("Représentant légal", "<p>［À COMPLÉTER : nom complet du représentant légal］</p>"),
  ("Responsable du contenu (art. 18 MStV)",
   "<p>［À COMPLÉTER : nom et adresse de la personne responsable du contenu de ce site］</p>"),
  ("Contact", "<p>E-mail : %s<br />WhatsApp : %s</p>" % (MAIL, WA)),
  ("Règlement des litiges de consommation",
   "<p>Nous ne sommes ni tenus ni disposés à participer à une procédure de règlement des litiges devant un organisme de médiation de la consommation.</p>"),
  ("Tribunal compétent / arbitrage",
   "<p>［À COMPLÉTER : droit applicable et tribunal compétent, ou clause d'arbitrage, si vous le souhaitez］</p>"
   "<p class=\"note\">Remarque : la plateforme européenne de règlement en ligne des litiges (ODR) a été arrêtée le 23 juillet 2025 et ne doit plus être citée.</p>"),
  ("Note sur le contenu",
   "<p>Toutes les informations de ce site sont fournies à titre d'informations produits B2B. Disponibilité, spécifications, délais et prix restent soumis à confirmation dans la demande concernée et dans la confirmation de commande écrite.</p>"),
 ]},
"it": {
 "title": "Note legali — SANFAN",
 "desc": "Note legali ai sensi dell'articolo 5 DDG e dell'articolo 18 MStV per FUJIAN SANFAN Sports Products Co., Ltd.",
 "h1": "Note legali",
 "lead": "Informazioni obbligatorie ai sensi dell'articolo 5 DDG e dell'articolo 18 MStV.",
 "secs": [
  ("Titolare del sito", OPERATOR),
  ("Legale rappresentante", "<p>［DA COMPILARE: nome completo del legale rappresentante］</p>"),
  ("Responsabile dei contenuti (art. 18 MStV)",
   "<p>［DA COMPILARE: nome e indirizzo della persona responsabile dei contenuti di questo sito］</p>"),
  ("Contatti", "<p>E-mail: %s<br />WhatsApp: %s</p>" % (MAIL, WA)),
  ("Risoluzione delle controversie di consumo",
   "<p>Non siamo tenuti né disponibili a partecipare a procedure di risoluzione delle controversie davanti a un organo di mediazione dei consumatori.</p>"),
  ("Foro competente / arbitrato",
   "<p>［DA COMPILARE: legge applicabile e foro competente, oppure clausola arbitrale, se desiderato］</p>"
   "<p class=\"note\">Nota: la piattaforma europea per la risoluzione online delle controversie (ODR) è stata soppressa il 23 luglio 2025 e non deve più essere citata.</p>"),
  ("Nota sui contenuti",
   "<p>Tutte le informazioni presenti su questo sito sono fornite come informazioni di prodotto B2B. Disponibilità, specifiche, tempi di consegna e variazioni di prezzo restano soggetti a conferma nella specifica richiesta e nella conferma d'ordine scritta.</p>"),
 ]},
"es": {
 "title": "Aviso legal — SANFAN",
 "desc": "Aviso legal conforme al artículo 5 DDG y al artículo 18 MStV de FUJIAN SANFAN Sports Products Co., Ltd.",
 "h1": "Aviso legal",
 "lead": "Información obligatoria conforme al artículo 5 DDG y al artículo 18 MStV.",
 "secs": [
  ("Titular del sitio web", OPERATOR),
  ("Representante legal", "<p>［PENDIENTE DE COMPLETAR: nombre completo del representante legal］</p>"),
  ("Responsable del contenido (art. 18 MStV)",
   "<p>［PENDIENTE DE COMPLETAR: nombre y dirección de la persona responsable del contenido de este sitio］</p>"),
  ("Contacto", "<p>Correo: %s<br />WhatsApp: %s</p>" % (MAIL, WA)),
  ("Resolución de litigios de consumo",
   "<p>No estamos obligados ni dispuestos a participar en procedimientos de resolución de controversias ante un órgano de mediación de consumo.</p>"),
  ("Órgano competente / arbitraje",
   "<p>［PENDIENTE DE COMPLETAR: ley aplicable y órgano competente, o cláusula de arbitraje, si lo desea］</p>"
   "<p class=\"note\">Nota: la plataforma europea de resolución de litigios en línea (ODR) se cerró el 23 de julio de 2025 y ya no debe citarse.</p>"),
  ("Nota sobre el contenido",
   "<p>Toda la información de este sitio se ofrece como información de producto B2B. La disponibilidad, las especificaciones, los plazos y los cambios de precio quedan sujetos a confirmación en la consulta concreta y en la confirmación de pedido por escrito.</p>"),
 ]},
}

# ── Privacy Policy ───────────────────────────────────────────────────────────
PRIVACY = {
"en": {
 "title": "Privacy Policy — SANFAN",
 "desc": "What we collect when you send an inquiry, who receives it, and what you can demand from us under the GDPR.",
 "h1": "Privacy Policy",
 "lead": "In plain language: what we collect, who receives it, and what you can demand.",
 "secs": [
  ("1. Who is responsible",
   "<p>%s, %s. Contact: %s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. What we collect when you send an inquiry",
   "<p>If you use the inquiry form we receive the data you enter: name, company, email address, product of interest, estimated quantity and message. We use this data solely to answer your inquiry and to prepare a quotation.</p>"
   "<p>The form is delivered through Formspree (formspree.io, United States), which acts as our technical processor. We do not use your data for advertising and we do not sell it.</p>"),
  ("3. Website usage data (Google Analytics)",
   "<p>We use Google Analytics 4 to understand which pages are used and how the site performs. It is loaded <strong>only after you consent</strong> in the consent banner at the bottom of the screen. If you decline, no analytics data is collected at all and the site works exactly the same. IP addresses are anonymised by Google.</p>"),
  ("4. Cookies and local storage",
   "<p>We set no advertising cookies. The only value stored in your browser is your consent decision, in localStorage under the key <code>sanfan_consent</code>. You can remove it at any time by clearing site data in your browser settings.</p>"),
  ("5. Hosting",
   "<p>This site is served as a static site from Vercel (vercel.com, United States). The hosting provider processes request data (time, requested file, IP address) for delivery, security and error analysis.</p>"),
  ("6. Your rights under the GDPR",
   "<p>You may request access to your data, correction, deletion, restriction, objection to processing, and portability. Send any request to %s. You also have the right to lodge a complaint with your local supervisory authority (in Germany: the Landesbeauftragte für Datenschutz und Freedom of Information of the state where the company is based).</p>" % MAIL),
  ("7. No data selling",
   "<p>We do not sell, rent out or trade personal data, and we share nothing with advertising networks.</p>"),
 ]},
"de": {
 "title": "Datenschutzerklärung — SANFAN",
 "desc": "Was wir bei einer Anfrage erheben, wer es erhält und welche Rechte Sie nach der DSGVO haben.",
 "h1": "Datenschutzerklärung",
 "lead": "Verständlich erklärt: was wir erheben, wer es bekommt und welche Rechte Sie haben.",
 "secs": [
  ("1. Verantwortliche Stelle",
   "<p>%s, %s. Kontakt: %s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. Welche Daten wir bei einer Anfrage erheben",
   "<p>Wenn Sie das Anfrageformular nutzen, erhalten wir die von Ihnen eingegebenen Daten: Name, Firma, E-Mail-Adresse, interessiertes Produkt, geschätzte Menge und Nachricht. Wir verwenden diese Daten ausschließlich zur Beantwortung Ihrer Anfrage und zur Erstellung eines Angebots.</p>"
   "<p>Das Formular wird über Formspree (formspree.io, USA) zugestellt, die als our technischer Dienstleister auftritt. Wir verwenden Ihre Daten nicht für Werbung und verkaufen sie nicht.</p>"),
  ("3. Nutzungsdaten der Website (Google Analytics)",
   "<p>Wir nutzen Google Analytics 4, um zu verstehen, welche Seiten genutzt werden und wie die Website läuft. Die Einbindung erfolgt <strong>nur nach Ihrer Einwilligung</strong> über die Einwilligungsleiste am unteren Bildschirmrand. Wenn Sie ablehnen, werden überhaupt keine Analyse-Daten erhoben und die Website funktioniert unverändert. IP-Adressen werden von Google anonymisiert.</p>"),
  ("4. Cookies und lokaler Speicher",
   "<p>Wir setzen keine Werbe-Cookies. Der einzige lokal gespeicherte Wert ist Ihre Einwilligungsentscheidung, im localStorage unter dem Schlüssel <code>sanfan_consent</code>. Sie können ihn jederzeit löschen, indem Sie die Websitedaten in Ihren Browser-Einstellungen löschen.</p>"),
  ("5. Hosting",
   "<p>Diese Website wird als statische Website über Vercel (vercel.com, USA) ausgeliefert. Der Hostinganbieter verarbeitet Anfragedaten (Zeitpunkt, angeforderte Datei, IP-Adresse) für Auslieferung, Sicherheit und Fehleranalyse.</p>"),
  ("6. Ihre Rechte nach der DSGVO",
   "<p>Sie können Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Widerspruch und Datenübertragbarkeit verlangen. Richten Sie Ihre Anfrage an %s. Sie haben außerdem das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren.</p>" % MAIL),
  ("7. Kein Datenverkauf",
   "<p>Wir verkaufen, vermieten oder handeln keine personenbezogenen Daten und geben nichts an Werbenetzwerke weiter.</p>"),
 ]},
"ja": {
 "title": "プライバシーポリシー — SANFAN",
 "desc": "お問い合わせで取得する情報、-information の受領先、GDPR に基づくお客様の権利。".replace("-information ", "する情報、"),
 "h1": "プライバシーポリシー",
 "lead": "わかりやすく HabitPostedします：取得する情報、その受領先、お客様の権利。".replace("HabitPosted", "説明します"),
 "secs": [
  ("1. 管理者", "<p>%s、%s。連絡先：%s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. お問い合わせ時に取得する情報",
   "<p>お問い合わせフォームをご利用の場合、入力された内容（氏名、会社名、メールアドレス、ご希望产品、数量の目安、ご質問）を取得します。これらの情報はお問い合わせへの回答と見積書の作成にのみ使用します。</p>"
   "<p>フォームは Formspree（formspree.io、米国）を経由して送信され、同社が技術的な受託者となります。広告利用や販売は一切行いません。</p>"),
  ("3. サイトの利用状況（Google Analytics）",
   "<p>どのページが利用されているか把握するため Google Analytics 4 を使用します。読み込みは画面下部の同意バナーで<strong>同意された場合にのみ</strong>行われます。拒否した場合は解析データは一切取得されず、サイトの機能は 동일합니다。IP アドレスは Google により匿名化されます。</p>"),
  ("4. Cookie とローカルストレージ",
   "<p>広告용 Cookie は使用しません。ブラウザに保存されるのは同意の選択内容のみで、localStorage の <code>sanfan_consent</code> というキーに記録されます。ブラウザの設定でサイトデータを削除すれば、いつでも消去できます。</p>"),
  ("5. ホスティング",
   "<p>本サイトは静的サイトとして Vercel（vercel.com、米国）から配信されます。ホスティング事業者が配信・セキュリティ・障害調査のためリクエスト情報（時刻、要求ファイル、IP アドレス）を処理します。</p>"),
  ("6. GDPR に基づくお客様の権利",
   "<p>開示、訂正、削除、処理の制限、処理への異議、データ移植を請求できます。請求は %s までご連絡ください。监督機関の Effective に異議を申し立てる権利もあります。</p>".replace("监督機関の Effective に", "所管の監督機関に")),
  ("7. データの販売はありません",
   "<p>個人データを販売・貸与・提供せず、広告ネットワークにも提供しません。</p>"),
 ]},
"ko": {
 "title": "개인정보처리방침 — SANFAN",
 "desc": "문의 시 수집하는 정보, 제공처, GDPR에 따른 고객의 권리 안내.",
 "h1": "개인정보처리방침",
 "lead": "알기 쉽게 안내합니다: 무엇을 수집하고, 누구에게 전달되며, 어떤 권리가 있는지.",
 "secs": [
  ("1. 개인정보 처리자", "<p>%s, %s. 문의: %s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. 문의 시 수집하는 정보",
   "<p>문의 양식을 이용하시면 입력하신 내용(성명, 회사명, 이메일, 관심 제품, 예상 수량, 문의 내용)을 전달받습니다. 이는 문의 답변과 견적 작성에만 사용합니다.</p>"
   "<p>양식은 Formspree(formspree.io, 미국)를 통해 전송되며, 해당 업체는 기술적 처리자로 작동합니다. 광고 활용이나 판매는 하지 않습니다.</p>"),
  ("3. 사이트 이용 데이터(Google Analytics)",
   "<p>어떤 페이지가 많이 이용되는지 파악하기 위해 Google Analytics 4를 사용합니다. <strong>화면 하단 동의 배너에서 동의한 경우에만</strong> 로드됩니다. 거부하면 분석 데이터가 전혀 수집되지 않으며 사이트 기능은 동일합니다. IP 주소는 Google에 의해 익명화됩니다.</p>"),
  ("4. 쿠키와 로컬 저장소",
   "<p>광고용 쿠키를 사용하지 않습니다. 브라우저에 저장되는 값은 동의 여부뿐이며, localStorage의 <code>sanfan_consent</code> 키에 기록됩니다. 브라우저 설정에서 사이트 데이터를 삭제하면 언제든지 지울 수 있습니다.</p>"),
  ("5. 호스팅",
   "<p>본 사이트는 정적 사이트로 Vercel(vercel.com, 미국)에서 제공됩니다. 호스팅 사업자는 전송·보안·오류 분석을 위해 요청 정보(시각, 요청 파일, IP 주소)를 처리합니다.</p>"),
  ("6. GDPR에 따른 고객의 권리",
   "<p>열람, 정정, 삭제, 처리 제한, 이의제기, 데이터 이동권을 요청하실 수 있습니다. 요청은 %s 로 보내주십시오. 관할 감독기관에 이의를 신청할 권리도 있습니다.</p>" % MAIL),
  ("7. 데이터 판매 없음",
   "<p>개인정보를 판매·임대·교환하지 않으며 광고 네트워크에도 제공하지 않습니다.</p>"),
 ]},
"fr": {
 "title": "Politique de confidentialité — SANFAN",
 "desc": "Ce que nous collectons lors d'une demande, qui le reçoit, et vos droits au titre du RGPD.",
 "h1": "Politique de confidentialité",
 "lead": "En clair : ce que nous collectons, qui le reçoit et ce que vous pouvez exiger.",
 "secs": [
  ("1. Responsable du traitement",
   "<p>%s, %s. Contact : %s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. Données collectées lors d'une demande",
   "<p>Lorsque vous utilisez le formulaire de demande, nous recevons les données que vous saisissez : nom, société, adresse e-mail, produit recherché, quantité estimée et message. Nous les utilisons uniquement pour répondre à votre demande et établir un devis.</p>"
   "<p>Le formulaire est transmis via Formspree (formspree.io, États-Unis), qui intervient comme notre sous-traitant technique. Nous n'utilisons pas vos données à des fins publicitaires et ne les vendons pas.</p>"),
  ("3. Données d'utilisation du site (Google Analytics)",
   "<p>Nous utilisons Google Analytics 4 afin de comprendre quelles pages sont consultées et comment le site fonctionne. Il n'est chargé <strong>qu'après votre consentement</strong> via la bannière affichée en bas de l'écran. En cas de refus, aucune donnée d'analyse n'est collectée et le site fonctionne à l'identique. Les adresses IP sont anonymisées par Google.</p>"),
  ("4. Cookies et stockage local",
   "<p>Nous ne déposons aucun cookie publicitaire. La seule valeur enregistrée dans votre navigateur est votre choix de consentement, dans localStorage sous la clé <code>sanfan_consent</code>. Vous pouvez l'effacer à tout moment en supprimant les données de site dans les paramètres de votre navigateur.</p>"),
  ("5. Hébergement",
   "<p>Ce site est servi comme site statique par Vercel (vercel.com, États-Unis). L'hébergeur traite les données de requête (heure, fichier demandé, adresse IP) pour la livraison, la sécurité et l'analyse des erreurs.</p>"),
  ("6. Vos droits au titre du RGPD",
   "<p>Vous pouvez demander l'accès, la rectification, l'effacement, la limitation, l'opposition et la portabilité de vos données. Adressez votre demande à %s. Vous avez également le droit d'introduire une réclamation auprès de l'autorité de contrôle compétente.</p>" % MAIL),
  ("7. Aucune vente de données",
   "<p>Nous ne vendons, ne louons ni n'échangeons de données personnelles et ne partageons rien avec des réseaux publicitaires.</p>"),
 ]},
"it": {
 "title": "Informativa sulla privacy — SANFAN",
 "desc": "Cosa raccogliamo quando inviate una richiesta, chi la riceve e quali diritti avete secondo il GDPR.",
 "h1": "Informativa sulla privacy",
 "lead": "In chiaro: cosa raccogliamo, chi lo riceve e cosa potete chiedere.",
 "secs": [
  ("1. Titolare del trattamento",
   "<p>%s, %s. Contatti: %s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. Dati raccolti quando inviate una richiesta",
   "<p>Quando utilizzate il modulo di richiesta riceviamo i dati che inserite: nome, azienda, e-mail, prodotto di interesse, quantità stimata e messaggio. Li utilizziamo esclusivamente per rispondere alla vostra richiesta e preparare un preventivo.</p>"
   "<p>Il modulo viene trasmesso tramite Formspree (formspree.io, Stati Uniti), che opera come nostro fornitore tecnico. Non utilizziamo i vostri dati per pubblicità e non li vendiamo.</p>"),
  ("3. Dati di utilizzo del sito (Google Analytics)",
   "<p>Utilizziamo Google Analytics 4 per capire quali pagine vengono visitate e come il sito funziona. Viene caricato <strong>solo dopo il tuo consenso</strong> tramite il banner in fondo alla schermata. Se rifiuti, non viene raccolto alcun dato analitico e il sito funziona esattamente allo stesso modo. Gli indirizzi IP sono anonimizzati da Google.</p>"),
  ("4. Cookie e memoria locale",
   "<p>Non impostiamo cookie pubblicitari. L'unico valore memorizzato nel browser è la tua scelta, in localStorage con la chiave <code>sanfan_consent</code>. Puoi cancellarla in qualsiasi momento eliminando i dati del sito nelle impostazioni del browser.</p>"),
  ("5. Hosting",
   "<p>Questo sito è servito come sito statico da Vercel (vercel.com, Stati Uniti). Il fornitore di hosting tratta i dati delle richieste (ora, file richiesto, indirizzo IP) per la distribuzione, la sicurezza e l'analisi degli errori.</p>"),
  ("6. I tuoi diritti secondo il GDPR",
   "<p>Puoi chiedere accesso, rettifica, cancellazione, limitazione, opposizione e portabilità dei tuoi dati. Scrivi a %s. Hai inoltre il diritto di proporre reclamo all'autorità di controllo competente.</p>" % MAIL),
  ("7. Nessuna vendita di dati",
   "<p>Non vendiamo, non affittiamo e non scambiamo dati personali e non condividiamo nulla con reti pubblicitarie.</p>"),
 ]},
"es": {
 "title": "Política de privacidad — SANFAN",
 "desc": "Qué recopilamos al enviar una consulta, quién la recibe y qué derechos tiene según el RGPD.",
 "h1": "Política de privacidad",
 "lead": "En lenguaje claro: qué recopilamos, quién lo recibe y qué puede exigirnos.",
 "secs": [
  ("1. Responsable del tratamiento",
   "<p>%s, %s. Contacto: %s</p>" % (F["name"], F["addr"], MAIL)),
  ("2. Qué recopilamos al enviar una consulta",
   "<p>Cuando utiliza el formulario de consulta recibimos los datos que introduce: nombre, empresa, correo electrónico, producto de interés, cantidad estimada y mensaje. Los utilizamos únicamente para responder a su consulta y preparar un presupuesto.</p>"
   "<p>El formulario se envía a través de Formspree (formspree.io, Estados Unidos), que actúa como nuestro encargado técnico. No utilizamos sus datos para publicidad ni los vendemos.</p>"),
  ("3. Datos de uso del sitio (Google Analytics)",
   "<p>Utilizamos Google Analytics 4 para saber qué páginas se utilizan y cómo funciona el sitio. Se carga <strong>solo después de su consentimiento</strong> mediante el banner que aparece en la parte inferior. Si lo rechaza, no se recopila ningún dato analítico y el sitio funciona exactamente igual. Google anonimiza las direcciones IP.</p>"),
  ("4. Cookies y almacenamiento local",
   "<p>No establecemos cookies publicitarios. El único valor que se guarda en su navegador es su decisión de consentimiento, en localStorage con la clave <code>sanfan_consent</code>. Puede borrarla en cualquier momento eliminando los datos del sitio en los ajustes de su navegador.</p>"),
  ("5. Alojamiento",
   "<p>Este sitio se sirve como sitio estático desde Vercel (vercel.com, Estados Unidos). El proveedor de alojamiento trata los datos de la petición (hora, archivo solicitado, dirección IP) para la entrega, la seguridad y el análisis de errores.</p>"),
  ("6. Sus derechos según el RGPD",
   "<p>Puede solicitar acceso, rectificación, supresión, limitación, oposición y portabilidad de sus datos. Envíe su solicitud a %s. También tiene derecho a presentar una reclamación ante la autoridad de control competente.</p>" % MAIL),
  ("7. No vendemos datos",
   "<p>No vendemos, alquilamos ni intercambiamos datos personales y no compartimos nada con redes publicitarias.</p>"),
 ]},
}

PAGES = {"impressum": IMPRINT, "privacy": PRIVACY}


def url_for(page, d):
    return "%s/%s%s.html" % (BASE, (d + "/") if d else "", page)


def hreflang_block(page):
    out = []
    for d in DIRS:
        out.append('  <link rel="alternate" hreflang="%s" href="%s" />'
                   % (d if d else "en", url_for(page, d)))
    out.append('  <link rel="alternate" hreflang="x-default" href="%s" />' % url_for(page, ""))
    return "\n".join(out)


def json_ld(page, d, content):
    url = url_for(page, d)
    lang = d if d else "en"
    home = "https://fjsanfan.com/"
    crumb = [{"@type": "ListItem", "position": 1, "name": "Home", "item": home},
             {"@type": "ListItem", "position": 2, "name": content["h1"], "item": url}]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": home + "#organization",
             "name": F["name"], "alternateName": F["name_cn"], "url": home,
             "email": F["email"], "telephone": F["wa"],
             "address": {"@type": "PostalAddress",
                         "streetAddress": "No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town",
                         "addressLocality": "Jinjiang", "addressRegion": "Fujian",
                         "addressCountry": "CN"}},
            {"@type": "WebSite", "@id": home + "#website", "url": home,
             "name": "FUJIAN SANFAN", "publisher": {"@id": home + "#organization"},
             "inLanguage": lang},
            {"@type": "WebPage", "@id": url + "#webpage", "url": url,
             "name": content["title"], "description": content["desc"],
             "isPartOf": {"@id": home + "#website"},
             "about": {"@id": home + "#organization"},
             "inLanguage": lang,
             "breadcrumb": {"@id": url + "#breadcrumb"}},
            {"@type": "BreadcrumbList", "@id": url + "#breadcrumb",
             "itemListElement": crumb},
        ],
    }
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)


def build(d, page, content):
    shell_rel = ("%s/faq.html" % d) if d else "faq.html"
    shell = io.open(os.path.join(ROOT, shell_rel), encoding="utf-8").read()
    lang = d if d else "en"

    # ① head：title / description / canonical / hreflang
    h = re.sub(r"<title>.*?</title>",
               lambda m: "<title>%s</title>" % content["title"], shell, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + content["desc"].replace('"', "&quot;") + m.group(2),
               h, count=1)
    # og / twitter：外壳是 FAQ 页的，不改就会让分享卡片显示 FAQ 标题、
    # og:url 还指向 faq.html（社交分享会带错 URL）→ 必须一起换成法律页自己的
    def set_meta(pattern, value):
        nonlocal h
        h = re.sub(pattern, lambda m: m.group(1) + value.replace('"', "&quot;") + m.group(2),
                   h, count=1)
    set_meta(r'(<meta property="og:title" content=")[^"]*(")', content["title"])
    set_meta(r'(<meta property="og:description" content=")[^"]*(")', content["desc"])
    set_meta(r'(<meta property="og:url" content=")[^"]*(")', url_for(page, d))
    set_meta(r'(<meta name="twitter:title" content=")[^"]*(")', content["title"])
    set_meta(r'(<meta name="twitter:description" content=")[^"]*(")', content["desc"])

    # canonical 与整组 hreflang 一起替换
    h = re.sub(r'[ \t]*<link rel="canonical"[^>]*>\n', "", h, count=1)
    h = re.sub(r'[ \t]*<link rel="alternate" hreflang=[^>]*>\n', "", h)
    h = re.sub(r'(<meta name="description"[^>]*>\n)',
               r'\1  <link rel="canonical" href="%s" />\n%s\n'
               % (url_for(page, d), hreflang_block(page)), h, count=1)

    # ② JSON-LD：外壳是 FAQPage（11 KB 的 FAQ 结构化数据），
    #    留在法律页上等于告诉搜索引擎「这页是问答页」→ 换成 Organization + WebPage + BreadcrumbList
    h = re.sub(r'[ \t]*<script type="application/ld\+json">.*?</script>\n',
               '  <script type="application/ld+json">\n%s\n  </script>\n' % json_ld(page, d, content),
               h, count=1, flags=re.S)

    # ③ 语言切换器：外壳里指向 faq.html，留在法律页上会让买家一点语言就跳到 FAQ。
    #    （`.lang-menu` 内只含 <a>，所以它自己的 </div> 就是第一个闭合标签。）
    def fix_menu(m):
        return m.group(0).replace("faq.html", "%s.html" % page)
    h = re.sub(r'<div class="lang-menu">.*?</div>', fix_menu, h, count=1, flags=re.S)

    # ② 内容块：整段替换 </header> 与 <footer 之间的一切
    body = []
    body.append('  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">')
    body.append('    <div class="container hero-inner" style="padding:64px 0 40px;">')
    body.append('      <h1>%s</h1>' % content["h1"])
    body.append('      <p class="lead">%s</p>' % content["lead"])
    body.append('    </div>')
    body.append('  </section>')
    body.append('  <section class="section">')
    body.append('    <div class="container">')
    for t, b in content["secs"]:
        body.append('      <h2>%s</h2>' % t)
        body.append('      %s' % b)
    body.append('    </div>')
    body.append('  </section>')

    i = h.find("</header>")
    j = h.find("<footer")
    if i < 0 or j < 0 or j < i:
        raise SystemExit("外壳结构异常：找不到 </header> 或 <footer>（%s）" % shell_rel)
    h = h[: i + len("</header>")] + "\n" + "\n".join(body) + "\n  " + h[j:]
    return h


def validate():
    """生成前的硬闸：内容表有问题就拒绝生成，不产出半成品。

    2026-10-03 实测教训：这份表第一版里我打出了跨语言垃圾字符
    （日语段里混进中文/拼音），肉眼很难发现，但上线就是客户可见的法律文本错误。
    """
    errs = []
    for page, d in PAGES.items():
        counts = {}
        for lang, c in d.items():
            for key in ("title", "desc", "h1", "lead"):
                if not c.get(key, "").strip():
                    errs.append("%s/%s 缺少 %s" % (page, lang, key))
            counts[lang] = len(c.get("secs", []))
            for t, b in c.get("secs", []):
                s = b.strip()
                if not (s.startswith("<p") and s.endswith("</p>")):
                    errs.append("%s/%s 段落未用 <p> 包裹: %s" % (page, lang, t))
                for junk in ("(dict)", "AUS", "它承担", "RAMADAN", "nope", "承担义务"):
                    if junk in s:
                        errs.append("%s/%s 段落含生成垃圾 %r: %s" % (page, lang, junk, t))
        uniq = sorted(set(counts.values()))
        if len(uniq) > 1:
            errs.append("%s 各语言段落数不一致: %s" % (page, counts))
    if errs:
        print("✗ 内容表未通过校验（%d 项），拒绝生成：" % len(errs))
        for e in errs[:20]:
            print("   " + e)
        return False
    return True


def main():
    if not validate():
        return 1
    dry = "--dry-run" in sys.argv
    made = []
    for page in ("impressum", "privacy"):
        for d in DIRS:
            key = d if d else "en"
            content = PAGES[page][key]
            rel = ("%s/%s.html" % (d, page)) if d else ("%s.html" % page)
            html = build(d, page, content)
            made.append((rel, len(html)))
            if not dry:
                p = os.path.join(ROOT, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True) if "/" in rel else None
                io.open(p, "w", encoding="utf-8").write(html)
    print("生成页面 %d 个（%s）" % (len(made), "dry-run" if dry else "已写入"))
    for rel, n in made:
        print("   %-26s %6d B" % (rel, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
