"""
Standalone test execution script for TradingAgents integration verification.
Runs all Tier 1-4 tests directly and outputs summary report.
"""

import sys
import os

# Ensure Consensus Deck_AG is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import tests.test_tradingagents as test_ta
import tests.test_streamlit_app as test_app
import tests.test_adversarial_ui_stress as test_adv


def run_all_tests():
    print("=" * 70)
    print("RUNNING TRADINGAGENTS & STREAMLIT APP VERIFICATION TEST SUITE")
    print("=" * 70)

    ta_tests = [
        ("test_package_exports_and_version", test_ta.test_package_exports_and_version),
        ("test_default_config_structure", test_ta.test_default_config_structure),
        ("test_data_provider_fallback_generation", test_ta.test_data_provider_fallback_generation),
        ("test_data_provider_indicator_calculations", test_ta.test_data_provider_indicator_calculations),
        ("test_fundamental_analyst", test_ta.test_fundamental_analyst),
        ("test_technical_analyst", test_ta.test_technical_analyst),
        ("test_sentiment_analyst", test_ta.test_sentiment_analyst),
        ("test_bull_and_bear_researchers", test_ta.test_bull_and_bear_researchers),
        ("test_risk_manager_bounds", test_ta.test_risk_manager_bounds),
        ("test_portfolio_manager_synthesis", test_ta.test_portfolio_manager_synthesis),
        ("test_propagate_deterministic_offline", test_ta.test_propagate_deterministic_offline),
        ("test_propagate_with_custom_debate_rounds", test_ta.test_propagate_with_custom_debate_rounds),
        ("test_missing_or_corrupted_fields_handling", test_ta.test_missing_or_corrupted_fields_handling),
    ]

    # Parametrized multi-ticker tests
    tickers = ["AAPL", "NVDA", "MSFT", "GOOGL", "JPM"]
    for t in tickers:
        ta_tests.append((f"test_multi_ticker_propagation_consistency[{t}]", lambda t=t: test_ta.test_multi_ticker_propagation_consistency(t)))

    app_tests = [
        ("test_app_ast_syntax", test_app.test_app_ast_syntax),
        ("test_all_seven_tabs_defined_in_app", test_app.test_all_seven_tabs_defined_in_app),
        ("test_tradingagents_imports_in_app", test_app.test_tradingagents_imports_in_app),
        ("test_radar_chart_generation", test_app.test_radar_chart_generation),
        ("test_1click_launch_mechanisms_in_app", test_app.test_1click_launch_mechanisms_in_app),
        ("test_offline_ui_deliberation_contract", test_app.test_offline_ui_deliberation_contract),
    ]

    adv_tests = [
        ("test_radar_chart_all_zeros", test_adv.test_radar_chart_all_zeros),
        ("test_radar_chart_all_hundreds", test_adv.test_radar_chart_all_hundreds),
        ("test_radar_chart_asymmetric_extreme_values", test_adv.test_radar_chart_asymmetric_extreme_values),
        ("test_radar_chart_missing_and_empty_keys", test_adv.test_radar_chart_missing_and_empty_keys),
        ("test_radar_chart_special_characters_in_ticker", test_adv.test_radar_chart_special_characters_in_ticker),
        ("test_session_state_multi_ticker_isolation", test_adv.test_session_state_multi_ticker_isolation),
        ("test_session_state_unrendered_ticker_behavior", test_adv.test_session_state_unrendered_ticker_behavior),
        ("test_1click_ticker_sanitization_and_deduplication", test_adv.test_1click_ticker_sanitization_and_deduplication),
        ("test_custom_ticker_case_and_whitespace_handling", test_adv.test_custom_ticker_case_and_whitespace_handling),
        ("test_missing_api_key_graceful_fallback", test_adv.test_missing_api_key_graceful_fallback),
        ("test_empty_string_api_key_graceful_fallback", test_adv.test_empty_string_api_key_graceful_fallback),
        ("test_full_offline_network_failure_resilience", test_adv.test_full_offline_network_failure_resilience),
        ("test_all_project_python_files_ast_parse", test_adv.test_all_project_python_files_ast_parse),
    ]

    all_tests = ta_tests + app_tests + adv_tests
    passed = 0
    failed = 0

    print(f"\nDiscovered {len(all_tests)} tests across Tiers 1-4 & Adversarial Challenge Suite.\n")

    for name, func in all_tests:
        try:
            func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"TEST SUMMARY: {passed} PASSED, {failed} FAILED (Total: {len(all_tests)})")
    print(f"PASS RATE: {(passed / len(all_tests)) * 100:.1f}%")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED SUCCESSFULLY! Ready for production deployment.")
        sys.exit(0)


if __name__ == "__main__":
    run_all_tests()

