class PinValidator:
    def __call__(self, text: str):
        assert len(text) == 6, "Validation PIN should be of size 6."
        for char in text:
            assert char.isdigit(), "Validation PIN can only contain digits"
