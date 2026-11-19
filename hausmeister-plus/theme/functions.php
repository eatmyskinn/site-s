<?php
if (!defined('ABSPATH')) exit;
add_action('after_setup_theme', function(){ add_theme_support('title-tag'); add_theme_support('post-thumbnails'); });
add_action('wp_enqueue_scripts', function(){ wp_enqueue_style('hp', get_template_directory_uri().'/assets/site.css', [], '1.0.0'); });
function hp_ru(){ return is_page('ru'); }
function hp_t($de,$ru){ return hp_ru() ? $ru : $de; }
function hp_setting($key){ return trim((string)get_theme_mod('hp_'.$key,'')); }
function hp_copies(){ static $copies; if(!isset($copies)) $copies=json_decode(file_get_contents(get_template_directory().'/copy.json'),true)?:[]; return $copies; }
add_shortcode('hp_copy',function($atts){
 $key=sanitize_key($atts['key']??''); $copy=hp_copies()[$key]??null;
 return $copy ? wp_kses_post(get_theme_mod('hp_copy_'.$key,$copy['default'])) : '';
});
add_action('customize_register',function($c){
 foreach(['de'=>'Тексты и цены · DE','ru'=>'Тексты и цены · RU'] as $lang=>$title) $c->add_section('hp_copy_'.$lang,['title'=>$title,'priority'=>26]);
 foreach(hp_copies() as $key=>$copy){
  $c->add_setting('hp_copy_'.$key,['default'=>$copy['default'],'sanitize_callback'=>'wp_kses_post']);
  $c->add_control('hp_copy_'.$key,['section'=>'hp_copy_'.$copy['lang'],'label'=>$copy['label'],'type'=>'textarea']);
 }
});
add_shortcode('hp_quick_contacts', function(){
 $links='';
 if(hp_setting('phone')) $links.='<a class="button" href="tel:'.esc_attr(preg_replace('/[^+0-9]/','',hp_setting('phone'))).'">'.hp_t('Anrufen','Позвонить').' ↗</a>';
 if(hp_setting('whatsapp')) $links.='<a class="button secondary" href="https://wa.me/'.esc_attr(preg_replace('/\D/','',hp_setting('whatsapp'))).'">WhatsApp ↗</a>';
 return $links ? '<div class="hero-buttons quick-contacts">'.$links.'</div>' : '';
});
add_action('customize_register', function($c){
 $c->add_section('hp_contacts',['title'=>'Hausmeister Plus · контакты','priority'=>25]);
 foreach(['phone'=>'Телефон (+49…)','whatsapp'=>'WhatsApp (цифры с кодом страны)','email'=>'Почта для заявок','impressum'=>'Ссылка Impressum','privacy'=>'Ссылка Datenschutz'] as $key=>$label){
  $sanitize = $key==='email' ? 'sanitize_email' : (in_array($key,['impressum','privacy']) ? 'esc_url_raw' : 'sanitize_text_field');
  $c->add_setting('hp_'.$key,['default'=>'','sanitize_callback'=>$sanitize]);
  $c->add_control('hp_'.$key,['section'=>'hp_contacts','label'=>$label,'type'=>'text']);
 }
});
add_shortcode('hp_form', function(){
 $ru=hp_ru(); $ready=hp_setting('email') && hp_setting('privacy'); ob_start();
 $status=isset($_GET['request']) ? sanitize_key($_GET['request']) : '';
 if($status) echo '<p class="notice" role="status">'.esc_html($status==='sent' ? hp_t('Vielen Dank! Ihre Anfrage wurde versendet.','Спасибо! Заявка отправлена.') : hp_t('Die Anfrage konnte nicht gesendet werden. Bitte versuchen Sie es später erneut.','Не удалось отправить заявку. Попробуйте позже.')).'</p>';
 ?>
 <form class="request-form" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" method="post" enctype="multipart/form-data">
 <input type="hidden" name="action" value="hp_request"><input type="hidden" name="lang" value="<?php echo $ru?'ru':'de'; ?>">
 <?php wp_nonce_field('hp_request','hp_nonce'); ?>
 <div class="trap" aria-hidden="true"><label>Website<input name="website" tabindex="-1" autocomplete="off"></label></div>
 <div class="form-row"><label><?php echo hp_t('Ihr Name','Ваше имя'); ?><input name="customer" required maxlength="100" autocomplete="name" placeholder="<?php echo hp_t('Vor- und Nachname','Имя и фамилия'); ?>"></label><label><?php echo hp_t('Telefon','Телефон'); ?><input name="phone" type="tel" required maxlength="40" autocomplete="tel" placeholder="+49 …"></label></div>
 <label><?php echo hp_t('Was können wir für Sie tun?','Что нужно сделать?'); ?><textarea name="message" required maxlength="4000" rows="4" placeholder="<?php echo hp_t('Zum Beispiel: einen Kleiderschrank aufbauen …','Например: собрать шкаф…'); ?>"></textarea></label>
 <label><?php echo hp_t('Adresse oder Postleitzahl','Адрес или индекс'); ?><input name="address" required maxlength="200" autocomplete="street-address" placeholder="Hamburg, 20095"></label>
 <label class="upload"><?php echo hp_t('＋ Foto hinzufügen (optional)','＋ Добавить фото (необязательно)'); ?><input type="file" name="photo" accept="image/jpeg,image/png,image/webp"><small>JPG, PNG, WebP · max. 5 MB</small></label>
 <label class="consent"><input type="checkbox" name="consent" value="1" required><span><?php echo hp_t('Ich stimme der Verarbeitung meiner Angaben zur Bearbeitung der Anfrage zu.','Согласен на обработку моих данных для ответа на заявку.'); ?> <?php if(hp_setting('privacy')) echo '<a href="'.esc_url(hp_setting('privacy')).'">Datenschutz</a>'; ?></span></label>
 <button class="button" type="submit" <?php disabled(!$ready); ?>><?php echo hp_t('Anfrage senden','Отправить заявку'); ?> <span>↗</span></button>
 <?php if(!$ready) echo '<p class="form-hint">'.hp_t('Vorschau: Der Versand wird nach Einrichtung der Kontakt- und Datenschutzangaben aktiviert.','Предпросмотр: отправка включится после настройки почты и страницы конфиденциальности.').'</p>'; ?>
 </form>
 <?php return ob_get_clean();
});
add_action('admin_post_nopriv_hp_request','hp_submit');
add_action('admin_post_hp_request','hp_submit');
function hp_submit(){
 $back=home_url(!empty($_POST['lang']) && $_POST['lang']==='ru' ? '/ru/' : '/');
 $finish=function($status) use($back){wp_safe_redirect(add_query_arg('request',$status,$back).'#anfrage');exit;};
 if($_SERVER['REQUEST_METHOD']!=='POST' || !isset($_POST['hp_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['hp_nonce'])),'hp_request')) $finish('error');
 if(!empty($_POST['website']) || empty($_POST['consent']) || !hp_setting('email') || !hp_setting('privacy')) $finish('error');
 $rate='hp_'.hash('sha256',($_SERVER['REMOTE_ADDR']??'').wp_salt());
 if(get_transient($rate)) $finish('error');
 $name=sanitize_text_field(wp_unslash($_POST['customer']??''));
 $phone=sanitize_text_field(wp_unslash($_POST['phone']??''));
 $address=sanitize_text_field(wp_unslash($_POST['address']??''));
 $message=sanitize_textarea_field(wp_unslash($_POST['message']??''));
 if(!$name || !$phone || !$address || !$message || strlen($message)>16000 || strlen($name)>400 || strlen($phone)>160 || strlen($address)>800) $finish('error');
 $attachment='';
 if(isset($_FILES['photo']) && $_FILES['photo']['error']!==UPLOAD_ERR_NO_FILE){
  $file=$_FILES['photo'];
  if($file['error']!==UPLOAD_ERR_OK || $file['size']>5*1024*1024 || !is_uploaded_file($file['tmp_name'])) $finish('error');
  require_once ABSPATH.'wp-admin/includes/file.php';
  $types=['jpg|jpeg'=>'image/jpeg','png'=>'image/png','webp'=>'image/webp'];
  $check=wp_check_filetype_and_ext($file['tmp_name'],$file['name'],$types);
  if(empty($check['ext']) || !in_array(wp_get_image_mime($file['tmp_name']),array_values($types),true)) $finish('error');
  $attachment=wp_tempnam('hausmeister-photo.'.$check['ext']);
  if(!$attachment || !move_uploaded_file($file['tmp_name'],$attachment)) {if($attachment)@unlink($attachment);$finish('error');}
 }
 set_transient($rate,1,60);
 $sent=wp_mail(hp_setting('email'),'Hausmeister Plus — neue Anfrage',"Name: $name\nTelefon: $phone\nAdresse: $address\n\n$message",[], $attachment ? [$attachment] : []);
 if($attachment) unlink($attachment);
 $finish($sent?'sent':'error');
}
