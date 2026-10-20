<?php
/**
 * Plugin Name:       BD e-Return
 * Plugin URI:        https://github.com/examresult29/claudeashad
 * Description:       Bangladesh individual income tax return calculator. Works out the tax as you type and prints the 12-page return (IT-11GA 2023 with Schedules 1-5, IT-10BB, IT-10B, tax computation and tax-free income sheets) as a PDF. Add it to a page with the [bd_e_return] shortcode, or use the e-Return admin menu.
 * Version:           1.0.0
 * Requires at least: 5.8
 * Requires PHP:      7.4
 * Author:            examresult29
 * License:           GPL-3.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-3.0.html
 * Text Domain:       bd-e-return
 *
 * The calculation and the PDF are made in the visitor's browser: no taxpayer data
 * is sent to or stored on the server.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'BDER_VERSION', '1.0.0' );
define( 'BDER_FILE', __FILE__ );

/**
 * Tax rule profiles shipped in assets/data/rules. The first one is the default.
 *
 * @return string[]
 */
function bder_profiles() {
	return (array) apply_filters( 'bder_profiles', array( 'ay2026-27', 'sample-template', 'fo2025' ) );
}

/**
 * Register the form's scripts and styles (enqueued only where the form appears).
 */
function bder_register_assets() {
	$url = plugin_dir_url( BDER_FILE ) . 'assets/';
	wp_register_style( 'bder-app', $url . 'css/app.css', array(), BDER_VERSION );
	wp_register_script( 'bder-pdf-lib', $url . 'vendor/pdf-lib.min.js', array(), '1.17.1', true );
	wp_register_script( 'bder-fontkit', $url . 'vendor/fontkit.umd.min.js', array(), '1.1.1', true );
	wp_register_script( 'bder-calc', $url . 'js/calc.js', array(), BDER_VERSION, true );
	wp_register_script( 'bder-render', $url . 'js/render.js', array( 'bder-pdf-lib', 'bder-fontkit' ), BDER_VERSION, true );
	wp_register_script( 'bder-app', $url . 'js/app.js', array( 'bder-calc', 'bder-render' ), BDER_VERSION, true );

	$profiles = array_values( bder_profiles() );
	$config   = array(
		'assetsUrl'      => $url,
		'profiles'       => $profiles,
		'defaultProfile' => apply_filters( 'bder_default_profile', $profiles[0] ),
		'assessmentYear' => apply_filters( 'bder_assessment_year', '2026-2027' ),
	);
	wp_add_inline_script( 'bder-app', 'window.BDER_CONFIG = ' . wp_json_encode( $config ) . ';', 'before' );
}
add_action( 'wp_enqueue_scripts', 'bder_register_assets' );
add_action( 'admin_enqueue_scripts', 'bder_register_assets' );

/**
 * The element the form is built into.
 *
 * @param string $profile Optional rules profile to preselect.
 * @return string HTML.
 */
function bder_container( $profile = '' ) {
	wp_enqueue_style( 'bder-app' );
	wp_enqueue_script( 'bder-app' );

	$attrs = ' data-base="' . esc_url( plugin_dir_url( BDER_FILE ) . 'assets/' ) . '"';
	if ( $profile && in_array( $profile, bder_profiles(), true ) ) {
		$attrs .= ' data-profile="' . esc_attr( $profile ) . '"';
	}
	return '<div class="bder-app"' . $attrs . '><noscript>'
		. esc_html__( 'The e-Return form needs JavaScript.', 'bd-e-return' )
		. '</noscript></div>';
}

/**
 * Shortcode: [bd_e_return profile="ay2026-27" login="yes"]
 *
 * @param array|string $atts Shortcode attributes.
 * @return string HTML.
 */
function bder_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'profile' => '',
			'login'   => 'no',
		),
		$atts,
		'bd_e_return'
	);

	if ( 'yes' === strtolower( $atts['login'] ) && ! is_user_logged_in() ) {
		return '<p class="bder-login">' . sprintf(
			/* translators: %s: login URL */
			wp_kses( __( 'Please <a href="%s">log in</a> to use the e-Return form.', 'bd-e-return' ), array( 'a' => array( 'href' => array() ) ) ),
			esc_url( wp_login_url( get_permalink() ) )
		) . '</p>';
	}
	return bder_container( sanitize_key( $atts['profile'] ) );
}
add_shortcode( 'bd_e_return', 'bder_shortcode' );

/**
 * Admin menu page with the same form.
 */
function bder_admin_menu() {
	add_menu_page(
		__( 'e-Return', 'bd-e-return' ),
		__( 'e-Return', 'bd-e-return' ),
		apply_filters( 'bder_capability', 'edit_posts' ),
		'bd-e-return',
		'bder_admin_page',
		'dashicons-media-spreadsheet',
		30
	);
}
add_action( 'admin_menu', 'bder_admin_menu' );

/**
 * Render the admin page.
 */
function bder_admin_page() {
	echo '<div class="wrap"><h1 class="screen-reader-text">' . esc_html__( 'e-Return', 'bd-e-return' ) . '</h1>';
	echo bder_container(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- built from escaped parts.
	echo '<p class="description" style="max-width:1240px;margin:12px auto">'
		. esc_html__( 'To put this form on a page, add the shortcode [bd_e_return]. Use [bd_e_return login="yes"] to show it only to logged-in users.', 'bd-e-return' )
		. '</p></div>';
}

/**
 * "Open" link on the Plugins screen.
 *
 * @param string[] $links Existing links.
 * @return string[]
 */
function bder_action_links( $links ) {
	array_unshift( $links, '<a href="' . esc_url( admin_url( 'admin.php?page=bd-e-return' ) ) . '">' . esc_html__( 'Open', 'bd-e-return' ) . '</a>' );
	return $links;
}
add_filter( 'plugin_action_links_' . plugin_basename( BDER_FILE ), 'bder_action_links' );
