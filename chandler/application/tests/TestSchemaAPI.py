import unittest
this_module = "application.tests.TestSchemaAPI"     # change this if it moves

def test_schema_api():
    import doctest
    return doctest.DocFileSuite(
        'schema_api.txt', optionflags=doctest.ELLIPSIS, package='application',
    )


if __name__=='__main__':
    # This module can't be safely run as __main__, so it has to be re-imported
    # and have *that* copy run.
    unittest.main(
        module=None,
        argv=["unittest", this_module+".test_schema_api"]
    )
else:
    assert __name__ == this_module, (
        "This module must be installed in its designated location"
    )
